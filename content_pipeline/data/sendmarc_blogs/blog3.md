# Cloudflare DMARC guidance + new SPF and DKIM requirements

Phishing, spoofing, and Spam continue to threaten organizations’ reputations and security. To reduce these risks, email authentication protocols such as Sender Policy Framework (SPF), DomainKeys Identified Mail (DKIM), and Domain-based Message Authentication, Reporting, and Conformance (DMARC) have become essential.

In June 2025, Cloudflare introduced a new requirement for all messages sent through its Email Routing service: They must pass either SPF or DKIM authentication checks by July 3, 2025. Cloudflare also strongly recommends that all senders implement DMARC.

This update reflects a broader industry trend focused on enforcing stricter email authentication policies. The growing adoption is possibly due to the increase in cyberthreats. In 2023, it was reported that cybercrime is expected to cost the world over $23 trillion by 2027.

## Understanding the Cloudflare DMARC, SPF, and DKIM announcement

Before examining Cloudflare’s new policy, it’s important to understand how SPF, DKIM, and DMARC protect domains from abuse.

### What is SPF?
SPF lets domain owners specify which IP addresses are authorized to send messages on their behalf. When a message arrives, the recipient’s email server checks the sender’s IP address against the SPF record in the DNS. If the IP address is listed, the email passes SPF authentication.

### What is DKIM?
DKIM adds a digital signature to the email header using a private key. The recipient verifies this signature using the public key published in the DNS. DKIM ensures that the email content hasn’t been altered during transit.

### What is DMARC?
DMARC builds on SPF and DKIM by allowing domain owners to publish policies that tell receiving servers how to handle emails that fail authentication. DMARC also provides reporting, giving businesses visibility into how their domains are being used.

DMARC policies can be configured to:
* **None** – Monitors email traffic without taking action.
* **Quarantine** – Sends suspicious messages to Spam or Junk folders.
* **Reject** – Blocks messages that fail authentication.

## Examining the Cloudflare DMARC, SPF, and DKIM update

Effective July 3, 2025, Cloudflare requires that all messages sent through its Email Routing platform must pass either SPF or DKIM authentication checks. Emails without SPF and DKIM will be forwarded to upstream mailbox providers. Cloudflare also suggests that every sender configure DMARC.

This change reflects Cloudflare’s commitment to improving email security. It also aligns with the policies of major email providers, including Google, Microsoft, and Yahoo, which already enforce strict authentication requirements to protect users.

### Why is Cloudflare making this change?

The Cloudflare SPF and DKIM requirements aim to:
* **Combat Spam and phishing:** Enforcing SPF or DKIM helps reduce the number of fraudulent emails sent through Cloudflare’s service.
* **Protect recipients and domains:** Authentication ensures emails are trustworthy, reducing cyber risk for both senders and recipients.
* **Align with industry standards:** The Cloudflare DKIM and SPF update helps meet email authentication best practices, supporting secure delivery and domain reputation.

## Simplify compliance with expert support

Navigating email authentication can be complex, but it doesn’t have to be. Sendmarc helps companies streamline SPF, DKIM, and DMARC implementation with expert tools and provides guidance every step of the way.

## How to prepare: Simplify Cloudflare DMARC, SPF, and DKIM compliance

To prevent email delivery disruptions and maintain secure communication, it’s essential to review and update your organization’s email authentication setup.

### Step 1: Deploy a DMARC policy

Publish a DMARC record in your DNS to define your policy and reporting preferences.
* Start with a monitoring policy (p=none) to gather data without affecting email delivery.
* Gradually move to an enforcement policy (p=quarantine and eventually p=reject) after verifying that all legitimate sources are configured.

**Example DMARC record:**
`_dmarc.yourdomain.com TXT v=DMARC1; p=reject; rua=mailto:dmarc-reports@yourdomain.com; fo=1;`

### Step 2: Configure SPF records correctly

* Identify all servers and services authorized to send emails on behalf of the domain.
* Create or update your SPF DNS TXT record to include those IP addresses and sending platforms.
* Use SPF validation tools to check for syntax errors and ensure all legitimate sources are included.

**Example SPF record:**
`@ TXT v=spf1 ip4:192.168.0.1 include:mail.example.com -all`

### Step 3: Implement DKIM signing

* Enable DKIM signing through your email service provider.
* Publish the DKIM public key as a TXT record in your DNS.
* Use a DKIM record checker to confirm that outgoing emails are signed.

**Example DKIM record:**
`selector._domainkey.yourdomain.com TXT v=DKIM1; k=rsa; p=[YourPublicKeyHere]`

At Sendmarc, we simplify the process of DMARC, SPF, and DKIM implementation, allowing you to experience the benefits of advanced email security without the effort.

## Why the Cloudflare DMARC recommendation is likely being introduced

Email providers are increasingly rejecting unauthenticated messages to protect users from cyberthreats.

By following the Cloudflare DMARC recommendation, you can:

### Protect your brand and customers
Phishing attacks often impersonate trusted domains to steal credentials or deliver malware. DMARC enforcement blocks unauthorized use of your business’s domain, helping protect its reputation and customers.
Earlier this year, 72% of companies globally reported an increase in cyber risks, showcasing the need for stronger defenses.

### Improve email deliverability
Emails that pass SPF, DKIM, and DMARC checks are more likely to reach inboxes, instead of being marked as Spam or Junk.

### Enhance visibility and control
DMARC reports provide valuable insights into who’s sending emails on your behalf. With this data, you can detect unauthorized senders and take action to prevent abuse.

## Best practices to meet the Cloudflare DMARC, SPF, and DKIM guidance

To meet the Cloudflare DMARC, SPF, and DKIM guidance, follow these best practices:

### Conduct a comprehensive email audit
Identify every service, platform, or team that sends email using your domain.

### Update DNS records carefully
Ensure SPF and DKIM records are accurate and up to date.
Avoid publishing multiple SPF records for the same domain.

### Monitor DMARC reports regularly
Review reports to spot legitimate sources that might require authentication updates.

## Common challenges and solutions

**Emails failing authentication**
Often caused by missing or misconfigured SPF or DKIM records. Run an analysis of the headers of the failing emails via our diagnostic tool to identify and resolve issues.

**Delayed DNS propagation**
DNS changes can take up to 48 hours to propagate globally. Schedule updates with this delay in mind.

**Multiple DMARC/SPF records**
Only one DMARC and one SPF record are allowed per domain. Merge any overlapping configurations to avoid problems.

## Act now to secure your email domain

The new Cloudflare SPF and DKIM requirements are a significant advancement in email security. It highlights the increasing importance of email authentication. By configuring and maintaining SPF, DKIM, and DMARC, you can:
* Protect your domain from spoofing and abuse
* Improve email deliverability and trust
* Strengthen your organization’s security posture

## Enhance your email security with expert support

Partner with specialists who understand the landscape and can guide you through every step. Sendmarc offers end-to-end DMARC management to help you:
* Visualize and interpret DMARC reports
* Automate policy enforcement
* Strengthen domain protection and reputation

