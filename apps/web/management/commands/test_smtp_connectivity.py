import smtplib
import ssl
import sys

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Test raw SMTP connectivity using smtplib directly. Bypasses Django's email backend."

    def handle(self, *args, **options):
        host = getattr(settings, "EMAIL_HOST", "") or "smtp.gmail.com"
        port = int(getattr(settings, "EMAIL_PORT", 587) or 587)
        user = getattr(settings, "EMAIL_HOST_USER", "") or ""
        password = getattr(settings, "EMAIL_HOST_PASSWORD", "") or ""
        use_tls = getattr(settings, "EMAIL_USE_TLS", True)
        use_ssl = getattr(settings, "EMAIL_USE_SSL", False)
        timeout = int(getattr(settings, "EMAIL_TIMEOUT", 10) or 10)

        self.stdout.write("SMTP connectivity test")
        self.stdout.write(f"  host     : {host}")
        self.stdout.write(f"  port     : {port}")
        self.stdout.write(f"  user     : {user or '<not set>'}")
        self.stdout.write(f"  password : {'<set>' if password else '<not set>'}")
        self.stdout.write(f"  tls      : {use_tls}")
        self.stdout.write(f"  ssl      : {use_ssl}")
        self.stdout.write(f"  timeout  : {timeout}s")
        self.stdout.write("")

        context = ssl.create_default_context()

        try:
            if use_ssl:
                self.stdout.write(f"Connecting to {host}:{port} via SSL...")
                server = smtplib.SMTP_SSL(host, port, timeout=timeout, context=context)
            else:
                self.stdout.write(f"Connecting to {host}:{port}...")
                server = smtplib.SMTP(host, port, timeout=timeout)
            server.set_debuglevel(1)
            self.stdout.write("Connected.")

            if not use_ssl and use_tls:
                self.stdout.write("Starting TLS...")
                server.starttls(context=context)
                self.stdout.write("TLS started.")

            if user and password:
                self.stdout.write(f"Attempting login as {user}...")
                server.login(user, password)
                self.stdout.write("Login successful.")
            else:
                self.stdout.write("No EMAIL_HOST_USER/PASSWORD set; skipping login test.")

            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("SMTP connectivity test passed."))
            server.quit()
        except Exception as e:
            self.stdout.write("")
            self.stdout.write(self.style.ERROR(f"SMTP connectivity test failed: {type(e).__name__}: {e}"))
            sys.exit(1)
