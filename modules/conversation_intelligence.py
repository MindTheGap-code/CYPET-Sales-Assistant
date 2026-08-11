import re


class ConversationIntelligence:
    """
    Lightweight commercial conversation analysis for CYPET Sales Assistant.

    Language is deliberately restricted to IT / EN:
    - Italian conversation -> IT
    - everything else -> EN

    The class works from Outlook message subjects/bodies and does not send
    messages. It provides a structured commercial brief that can later be
    passed to an LLM without changing the Actions/Outlook workflow.
    """

    ITALIAN_MARKERS = {
        "buongiorno", "buonasera", "grazie", "grazie mille", "salve",
        "ciao", "certo", "nessun problema",
        "ciao", "vorrei", "abbiamo", "abbiamo parlato", "incontro",
        "ieri", "oggi", "domani", "progetto", "contenitore", "contenitori",
        "bottiglia", "bottiglie", "prezzo", "offerta", "preventivo",
        "interessato", "interessati", "interesse", "possibile",
        "possibilità", "necessità", "esigenza", "sviluppo", "produzione",
        "azienda", "potete", "possiamo", "vorremmo", "richiesta",
        "richiediamo", "discutere", "sentiamoci", "chiamata", "call",
    }

    POSITIVE_MARKERS = {
        "interested", "interest", "interessato", "interessati",
        "interesse", "interesting", "sounds good", "looks good",
        "we would like", "vorremmo", "ci interessa", "siamo interessati",
        "possibile", "possibilità", "let's discuss", "discutere",
        "call", "meeting", "incontro", "call me", "sentiamoci",
        "certo", "nessun problema", "sure", "no problem", "of course",
        "yes", "si", "sì", "va bene", "ok", "okay", "happy to", "glad to",
    }

    NEGATIVE_MARKERS = {
        "not interested", "no interest", "not relevant", "not needed",
        "non interessato", "non siamo interessati", "non ci interessa",
        "non necessario", "non ci serve", "no longer", "closed",
    }

    WAITING_MARKERS = {
        "need to evaluate", "need to check", "need to discuss",
        "will evaluate", "will check", "let me check", "get back to you",
        "come back to you", "we will let you know", "waiting",
        "da valutare", "devo verificare", "dobbiamo valutare",
        "ci aggiorniamo", "ti faccio sapere", "vi faremo sapere",
        "verificare", "valutare", "approvazione",
    }

    REQUEST_MARKERS = {
        "please send", "send me", "could you", "can you", "please provide",
        "quotation", "quote", "offer", "proposal", "datasheet",
        "specification", "specifications", "information",
        "mandami", "inviami", "potete inviare", "potresti inviare",
        "preventivo", "offerta", "proposta", "scheda tecnica",
        "specifiche", "informazioni",
    }


    @classmethod
    def analyze_thread(
        cls,
        contact_name="",
        company="",
        messages=None,
        fallback_sent_subject="",
        fallback_sent_body="",
        fallback_reply_subject="",
        fallback_reply_body="",
    ):
        """
        Analyze an ordered conversation thread.

        messages is expected as a list of dictionaries:
        {
            "direction": "sent" | "received",
            "subject": str,
            "body": str,
            "date": optional comparable/display value,
        }

        The method deliberately separates:
        - email subject
        - actual thread content
        - commercial topic
        - customer position
        - next objective
        - confidence

        If the thread does not support a commercial conclusion, the result
        says so instead of inventing one.
        """
        thread = []
        for message in (messages or []):
            body = cls._clean_signature(message.get("body", ""))
            subject = cls._clean_subject(message.get("subject", ""))
            if not body and not subject:
                continue

            thread.append({
                "direction": (
                    "received"
                    if str(message.get("direction", "")).lower()
                    in ("received", "incoming", "customer")
                    else "sent"
                ),
                "subject": subject,
                "body": body,
                "date": message.get("date"),
            })

        # Most recent customer reply / CYPET message.
        received = [m for m in thread if m["direction"] == "received"]
        sent = [m for m in thread if m["direction"] == "sent"]

        last_received = received[-1] if received else None
        last_sent = sent[-1] if sent else None

        reply_subject = (
            last_received["subject"] if last_received else fallback_reply_subject
        )
        reply_body = (
            last_received["body"] if last_received else fallback_reply_body
        )
        sent_subject = (
            last_sent["subject"] if last_sent else fallback_sent_subject
        )
        sent_body = (
            last_sent["body"] if last_sent else fallback_sent_body
        )

        # Language is based primarily on the latest customer message.
        language = cls.detect_language(
            reply_body or reply_subject or sent_body or sent_subject
        )

        topic = cls._thread_topic(thread)
        customer_position = cls._customer_position(reply_body)
        open_point = cls._open_point(reply_body, sent_body)
        next_objective = cls._next_objective(
            reply_body,
            customer_position,
            open_point,
        )

        # A topic is "real" only when supported by thread content.
        confidence = cls._thread_confidence(
            thread=thread,
            topic=topic,
            customer_position=customer_position,
            open_point=open_point,
        )

        if confidence == "LOW":
            topic = ""

        return {
            "contact_name": contact_name or "",
            "company": company or "",
            "language": language,
            "topic": topic,
            "subject": (
                reply_subject
                or sent_subject
                or ""
            ),
            "thread_messages": len(thread),
            "customer_messages": len(received),
            "cypet_messages": len(sent),
            "thread": [
                {
                    "direction": m["direction"],
                    "subject": m["subject"],
                    "body": m["body"],
                }
                for m in thread
            ],
            "what_cypet_proposed": cls._proposal(sent_body),
            "customer_position": customer_position,
            "open_point": open_point,
            "next_objective": next_objective,
            "next_contact_commitment": cls._next_contact_commitment(reply_body),
            "confidence": confidence,
            "context_status": (
                "sufficient"
                if confidence != "LOW"
                else "insufficient"
            ),
            "last_reply_subject": reply_subject or "",
            "last_reply_body": reply_body or "",
            "last_sent_subject": sent_subject or "",
            "last_sent_body": sent_body or "",
        }

    @classmethod
    def _clean_signature(cls, body):
        text = cls._clean(body)
        if not text:
            return ""

        # Outlook Body often contains the entire quoted previous message.
        # Remove quoted content before extracting topic/proposal. This is
        # critical because quoted subjects such as "Follow-up incontro di ieri"
        # are not commercial content.
        quote_markers = (
            r"(?im)^\s*-{2,}\s*original message\s*-{2,}\s*$",
            r"(?im)^\s*-{2,}\s*messaggio originale\s*-{2,}\s*$",
            r"(?im)^\s*from:\s+.+$",
            r"(?im)^\s*da:\s+.+$",
            r"(?im)^\s*sent:\s+.+$",
            r"(?im)^\s*inviato:\s+.+$",
            r"(?im)^\s*to:\s+.+$",
            r"(?im)^\s*a:\s+.+$",
            r"(?im)^\s*subject:\s+.+$",
            r"(?im)^\s*oggetto:\s+.+$",
            r"(?im)^\s*>+",
        )

        # Prefer the first clear quoted-message boundary.
        boundary_positions = []
        for pattern in quote_markers:
            match = re.search(pattern, text)
            if match:
                boundary_positions.append(match.start())

        if boundary_positions:
            text = text[:min(boundary_positions)].rstrip()

        lower = text.lower()

        # Outlook/Exchange may concatenate the reply and the contact signature
        # without a blank line. Detect common job-title/contact signatures even
        # when they are appended directly to the customer's sentence.
        compact_signature_patterns = (
            r"\bmerli\s+fausto\b.*\bresponsabile\s+acquisti\b",
            r"\bresponsabile\s+acquisti\b.*\bpurchasing\s+manager\b",
            r"\bresponsabile\s+tecnico\b.*\bpackag",
            r"\bpurchasing\s+manager\b.*\bresponsabile\s+tecnico\b",
        )
        compact_positions = []
        for pattern in compact_signature_patterns:
            match = re.search(pattern, lower, flags=re.IGNORECASE)
            if match:
                compact_positions.append(match.start())

        if compact_positions:
            text = text[:min(compact_positions)].rstrip()
            lower = text.lower()

        signature_markers = (
            "\nbusiness development executive for europe",
            "\nbusiness development executive",
            "\nsales manager",
            "\nresponsabile acquisti",
            "\nresponsabile tecnico",
            "\npurchasing manager",
            "\nmerli fausto",
            "\nfausto merli",
            "\nbest regards",
            "\nkind regards",
            "\ncordiali saluti",
            "\nun cordiale saluto",
            "\nregards,",
        )

        positions = [
            lower.find(marker)
            for marker in signature_markers
            if lower.find(marker) >= 0
        ]
        if positions:
            text = text[:min(positions)].rstrip()

        for marker in (
            "\nconfidentiality notice",
            "\nthis email and any attachments",
            "\nquesta e-mail",
        ):
            pos = text.lower().find(marker)
            if pos >= 0:
                text = text[:pos].rstrip()

        return text


    @classmethod
    def _thread_topic(cls, thread):
        """Commercial topic comes ONLY from cleaned message bodies."""
        combined = " ".join(
            cls._clean_signature(m.get("body", ""))
            for m in thread
        ).lower()

        topic_patterns = [
            (r"\b(?:pet|rpet)\s+(?:bottle|bottles|container|containers)\b",
             "PET bottle/container project"),
            (r"\bpreform(?:s)?\b", "preform project"),
            (r"\b(?:hot[- ]fill|hotfill)\b", "hot-fill project"),
            (r"\b(?:lightweighting|lightweight)\b", "lightweighting project"),
            (r"\b(?:pet ibc|ibc)\b", "PET IBC project"),
            (
                r"\b(?:pet|rpet)\s+(?:packaging|container|containers)\b",
                "PET packaging/container project",
            ),
        ]
        for pattern, label in topic_patterns:
            if re.search(pattern, combined):
                return label
        return ""


    @classmethod
    def _thread_confidence(
        cls,
        thread,
        topic,
        customer_position,
        open_point,
    ):
        if len(thread) < 2:
            return "LOW"

        meaningful_bodies = [
            cls._clean_signature(m.get("body", ""))
            for m in thread
            if cls._clean_signature(m.get("body", ""))
        ]

        if not meaningful_bodies:
            return "LOW"

        # Explicit customer-requested future contact point is strong evidence
        # even when the email subject is generic "Follow-up".
        commitment_text = (
            f"{customer_position or ''} {open_point or ''}"
        ).lower()

        explicit_commitment_markers = (
            "next contact point is mid-september",
            "explicitly asked to reconnect in mid-september",
            "mid-september",
            "mid september",
        )

        if any(marker in commitment_text for marker in explicit_commitment_markers):
            return "HIGH"

        # Without a supported commercial topic we do not have enough
        # context to claim HIGH/MEDIUM confidence.
        if not topic:
            return "LOW"

        if len(meaningful_bodies) >= 2:
            if (
                "positively accepted" in customer_position.lower()
                or "requesting information" in customer_position.lower()
            ):
                return "HIGH"
            return "MEDIUM"

        return "LOW"
    def analyze(
        cls,
        contact_name="",
        company="",
        last_sent_subject="",
        last_sent_body="",
        last_reply_subject="",
        last_reply_body="",
    ):
        return cls.analyze_thread(
            contact_name=contact_name,
            company=company,
            messages=[
                {
                    "direction": "sent",
                    "subject": last_sent_subject,
                    "body": last_sent_body,
                },
                {
                    "direction": "received",
                    "subject": last_reply_subject,
                    "body": last_reply_body,
                },
            ],
            fallback_sent_subject=last_sent_subject,
            fallback_sent_body=last_sent_body,
            fallback_reply_subject=last_reply_subject,
            fallback_reply_body=last_reply_body,
        )


    @classmethod
    def detect_language(cls, text):
        text = (text or "").lower()
        if not text:
            return "EN"

        score = 0
        for marker in cls.ITALIAN_MARKERS:
            if re.search(r"(?<!\w)" + re.escape(marker) + r"(?!\w)", text):
                score += 1

        # Italian morphology / function words provide useful additional
        # evidence without trying to classify other languages.
        score += len(re.findall(
            r"(?<!\w)(?:il|la|le|gli|un|una|che|con|per|del|della|dei|"
            r"sono|siamo|avete|abbiamo|potete|vorrei|vorremmo)(?!\w)",
            text,
        ))

        return "IT" if score >= 2 else "EN"

    @staticmethod
    def _clean(text):
        text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
        for marker in (
            "\n-----Original Message-----",
            "\nFrom:",
            "\nSent:",
            "\nDa:",
            "\nInviato:",
        ):
            if marker in text:
                text = text.split(marker, 1)[0]
        return text.strip()

    GENERIC_SUBJECT_PATTERNS = (
        r"\bfollow[- ]?up\b",
        r"\bchecking in\b",
        r"\breconnecting\b",
        r"\bquick follow[- ]?up\b",
        r"\bjust following up\b",
    )

    @classmethod
    def _clean_subject(cls, subject):
        subject = (subject or "").strip()
        # Strip Outlook reply/forward prefixes repeatedly, including short
        # forms such as "R:" used by some mail clients.
        subject = re.sub(
            r"^(?:(?:re|fw|fwd|r)\s*:\s*)+",
            "",
            subject,
            flags=re.IGNORECASE,
        ).strip()
        return subject

    @classmethod
    def is_generic_subject(cls, subject):
        clean = cls._clean_subject(subject).lower()
        if not clean:
            return True

        normalized = re.sub(
            r"[^a-z0-9àèéìòù\s-]",
            " ",
            clean,
        )
        normalized = re.sub(r"\s+", " ", normalized).strip()

        # Any subject whose semantic core is a follow-up/check-in is a
        # communication action, not a commercial topic.
        return any(
            re.search(pattern, normalized)
            for pattern in cls.GENERIC_SUBJECT_PATTERNS
        )


    @classmethod
    def _clean_signature(cls, body):
        text = cls._clean(body)
        if not text:
            return ""
        lower = text.lower()
        markers = (
            "\nbusiness development executive for europe",
            "\nbusiness development executive",
            "\nsales manager",
            "\nbest regards",
            "\nkind regards",
            "\ncordiali saluti",
            "\nun cordiale saluto",
            "\nregards,",
        )
        positions = [lower.find(marker) for marker in markers if lower.find(marker) >= 0]
        if positions:
            text = text[:min(positions)].rstrip()
        for marker in (
            "\nconfidentiality notice",
            "\nthis email and any attachments",
            "\nquesta e-mail",
        ):
            pos = text.lower().find(marker)
            if pos >= 0:
                text = text[:pos].rstrip()
        return text

    @classmethod
    def _topic(cls, reply_subject, sent_subject):
        reply_clean = cls._clean_subject(reply_subject)
        sent_clean = cls._clean_subject(sent_subject)
        if reply_clean and not cls.is_generic_subject(reply_clean):
            return reply_clean
        if sent_clean and not cls.is_generic_subject(sent_clean):
            return sent_clean
        return ""

    @classmethod
    def _customer_position(cls, reply):
        text = cls._clean_signature(reply).lower()
        if not text:
            return "No recent customer reply identified."

        if any(marker in text for marker in (
            "risentirci a metà settembre", "risentirci a meta settembre",
            "sentiamoci a metà settembre", "sentiamoci a meta settembre",
            "a metà settembre", "a meta settembre",
            "mid september", "in september",
            "let's reconnect in september",
            "let's speak in september",
            "get back to you in september",
        )):
            return "The customer wants to reconnect at a later time and the next contact point is mid-September."

        if any(marker in text for marker in cls.NEGATIVE_MARKERS):
            return "The customer is declining the topic or indicates that it is not currently relevant."

        if any(marker in text for marker in cls.REQUEST_MARKERS):
            return "The customer is engaging with the topic and is asking for information or a concrete next step."

        if any(marker in text for marker in cls.WAITING_MARKERS):
            return "The customer is keeping the topic open but is evaluating or waiting for the next internal step."

        if any(marker in text for marker in cls.POSITIVE_MARKERS):
            return "The customer shows positive engagement with the topic."

        return "The customer position is not explicit from the available reply."

    @classmethod
    def _proposal(cls, sent):
        if not sent:
            return "No recent CYPET message body was available."

        sentences = cls._sentences(sent)

        # Keep the most informative sentence(s), avoiding greetings/signatures.
        useful = []
        for sentence in sentences:
            low = sentence.lower()
            if len(sentence) < 35:
                continue
            if any(x in low for x in (
                "best regards", "kind regards", "regards", "cordiali saluti",
                "hello", "hi ", "buongiorno", "buonasera",
            )):
                continue
            useful.append(sentence.strip())

        if not useful:
            return "Recent CYPET communication available; proposal content requires review."

        return " ".join(useful[:2])

    @classmethod
    def _open_point(cls, reply, sent):
        reply_text = cls._clean_signature(reply).lower()
        text = reply_text + "\n" + cls._clean_signature(sent).lower()

        if any(marker in reply_text for marker in (
            "a metà settembre", "a meta settembre",
            "mid september", "in september",
        )):
            return "The customer explicitly asked to reconnect in mid-September."

        if any(marker in text for marker in cls.REQUEST_MARKERS):
            return "A customer request or missing information may still need to be addressed."

        if any(marker in text for marker in cls.WAITING_MARKERS):
            return "The customer's evaluation or next internal step is still open."

        return "No explicit open point was detected; the conversation should be reviewed before sending."

    @classmethod
    def _next_contact_commitment(cls, reply):
        text = cls._clean_signature(reply).lower()
        if any(marker in text for marker in (
            "a metà settembre", "a meta settembre",
            "mid september", "in september",
        )):
            return "MID-SEPTEMBER"
        return ""

    @classmethod
    def _next_objective(cls, reply, customer_position, open_point):
        text = cls._clean_signature(reply).lower()

        if any(marker in text for marker in (
            "a metà settembre", "a meta settembre",
            "mid september", "in september",
        )):
            return "Reconnect with the customer in mid-September, as requested."

        if any(marker in text for marker in cls.REQUEST_MARKERS):
            return "Address the customer's request and move the discussion to the requested concrete next step."

        if any(marker in text for marker in cls.WAITING_MARKERS):
            return "Reconnect on the pending evaluation and identify whether a technical or commercial next step can be agreed."

        if "call" in text or "meeting" in text or "incontro" in text:
            return "Confirm or propose the next call or meeting."

        return "Reconnect on the specific topic and propose a clear, low-friction next step."

    @staticmethod
    def _sentences(text):
        return [
            item.strip()
            for item in re.split(r"(?<=[.!?])\s+|\n+", text)
            if item.strip()
        ]
