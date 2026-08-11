import re
import win32com.client


class OutlookInboxReader:
    """Read Outlook Inbox messages and recent Sent Items."""

    INBOX_FOLDER = 6
    SENT_FOLDER = 5
    MAIL_ITEM_CLASS = 43

    def __init__(self):
        self.outlook = win32com.client.Dispatch("Outlook.Application")
        self.namespace = self.outlook.GetNamespace("MAPI")
        self.inbox = self.namespace.GetDefaultFolder(self.INBOX_FOLDER)
        self.sent = self.namespace.GetDefaultFolder(self.SENT_FOLDER)

    def get_last_messages(self, number=100):
        items = self.inbox.Items
        items.Sort("[ReceivedTime]", True)
        result = []

        for mail in items:
            if len(result) >= number:
                break
            try:
                if mail.Class != self.MAIL_ITEM_CLASS:
                    continue
                result.append(mail)
            except Exception:
                continue

        return result

    def get_last_sent_messages(self, number=100):
        items = self.sent.Items
        items.Sort("[SentOn]", True)
        result = []

        for mail in items:
            if len(result) >= number:
                break
            try:
                if mail.Class != self.MAIL_ITEM_CLASS:
                    continue
                result.append(mail)
            except Exception:
                continue

        return result

    @classmethod
    def sync_sent_to_database(cls, db, number=100):
        reader = cls()
        imported = 0

        try:
            for mail in reader.get_last_sent_messages(number):
                try:
                    outlook_id = str(mail.EntryID or "").strip()
                    if not outlook_id:
                        continue

                    sent_on = mail.SentOn
                    sent_date = (
                        sent_on.isoformat()
                        if hasattr(sent_on, "isoformat")
                        else str(sent_on)
                    )

                    recipients = reader._get_recipients(mail)
                    if not recipients:
                        continue

                    recipient_name, recipient_email = recipients[0]
                    domain = reader._domain_from_email(recipient_email)
                    subject = str(mail.Subject or "").strip()

                    if db.insert_email(
                        outlook_id=outlook_id,
                        sent_date=sent_date,
                        recipient_name=recipient_name,
                        recipient_email=recipient_email,
                        domain=domain,
                        subject=subject,
                    ):
                        imported += 1

                except Exception as exc:
                    print(f"Outlook sync: skipped message: {exc}")
                    continue
        finally:
            reader.close()

        return imported

    def _get_recipients(self, mail):
        result = []

        try:
            for recipient in mail.Recipients:
                try:
                    email = self._recipient_smtp(recipient)
                    if not email:
                        continue

                    if email.lower().endswith("@cypet.eu"):
                        continue

                    name = str(
                        getattr(recipient, "Name", "") or ""
                    ).strip()

                    result.append((name, email.lower()))
                except Exception:
                    continue
        except Exception:
            return []

        return result

    @staticmethod
    def _recipient_smtp(recipient):
        try:
            address = str(
                getattr(recipient, "Address", "") or ""
            ).strip()

            if address.upper().startswith("/O="):
                try:
                    exchange_user = recipient.AddressEntry.GetExchangeUser()
                    if exchange_user:
                        smtp = (
                            exchange_user.PrimarySmtpAddress or ""
                        ).strip()
                        if smtp:
                            return smtp
                except Exception:
                    pass

            if "@" in address:
                return address

            try:
                entry = recipient.AddressEntry
                if entry:
                    exchange_user = entry.GetExchangeUser()
                    if exchange_user:
                        return (
                            exchange_user.PrimarySmtpAddress or ""
                        ).strip()
            except Exception:
                pass
        except Exception:
            pass

        return ""

    @staticmethod
    def _domain_from_email(email):
        email = (email or "").strip().lower()
        if "@" not in email:
            return ""
        return email.rsplit("@", 1)[1]

    @staticmethod
    def normalize_subject(subject):
        subject = (subject or "").strip()
        subject = re.sub(
            r"^(?:(?:RE|FW|FWD)\s*:\s*)+",
            "",
            subject,
            flags=re.IGNORECASE,
        )
        return subject.strip().lower()

    @staticmethod
    def sender_smtp(mail):
        try:
            address = mail.SenderEmailAddress or ""

            if address.upper().startswith("/O="):
                sender = mail.Sender
                if sender:
                    exchange_user = sender.GetExchangeUser()
                    if exchange_user:
                        return (
                            exchange_user.PrimarySmtpAddress or ""
                        ).lower()

            return address.lower()
        except Exception:
            return ""

    def close(self):
        self.outlook = None
        self.namespace = None
        self.inbox = None
        self.sent = None
