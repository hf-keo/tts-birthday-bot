# Monochrome Birthday Bot — Privacy Policy

Effective date: 13 November 2026

## Scope and operator
This policy describes the birthday-bot functionality of Discord application 1026321174315147395, Monochrome Birthday Bot, operated by the maintainer of [hf-keo/tts-birthday-bot](https://github.com/hf-keo/tts-birthday-bot), GitHub account hf-keo. It covers this operator’s instance, not independently hosted copies or Discord’s own services. It does not describe the application’s former GPT functionality.

## Information processed
The bot’s SQLite database stores:

- Your Discord user ID, the server (guild) ID, and the birthday day and month submitted by you or an administrator. Birth year and age are not collected by the birthday form.
- Server settings: announcement channel ID, optional role ID, mention preference, and whether announcements are enabled.
- Delivery history: server ID, user ID, the calendar date of an attempted birthday announcement, and its pending/sent status, to prevent duplicate announcements. This date is a delivery date, not your birth year.

The bot also processes Discord command and modal inputs, permissions, channel/role information, membership status, and display names as needed to respond and send announcements. Application or hosting logs may include timestamps, errors, and user/server IDs. The birthday code does not intentionally persist ordinary chat messages, voice recordings, payment information, or contact lists, and does not send birthday data to an AI service. Discord and the hosting provider may process their own service and connection logs.

## Purposes and visibility
Information is used to maintain each server’s calendar, respond to commands, deliver birthday wishes, prevent duplicates, and diagnose failures. Registration is voluntary. Administrators should obtain your permission before registering a birthday for you.

Your birthday day/month and Discord identity are available to members of the same server through /birthday list and /birthday upcoming. Although command replies are ephemeral, other members can run those commands. Announcements are visible to anyone who can access the configured channel and may mention you or a selected role. Other users may retain copies of messages they can see. Database records are separated by server ID.

## Storage, access, and sharing
Records are stored on the bot’s host. The operator and hosting provider may access stored data or logs as necessary to run, support, and secure the service. Discord receives interactions and announcement messages under its [Privacy Policy](https://discord.com/privacy). Hosting may involve processing outside your country; no specific storage country is promised.

The birthday bot has no advertising, data-sale, or third-party analytics feature. Data is not used for marketing or AI training by this birthday service. Information may be disclosed when legally required or necessary to address abuse or security incidents. Reasonable access controls should protect the host and credentials, but no system can guarantee absolute security.

## Retention and your choices
Use /birthday register to correct your day/month and /birthday remove to delete your birthday entry in each server where you registered. Administrators can remove a member’s entry with /birthday admin-remove. The bot removes an absent member’s birthday when that member’s scheduled birthday is checked; leaving a server or uninstalling the bot does not immediately erase all records.

The current code has no automatic expiry for server settings or delivery history. Removing a birthday does not delete delivery-history records, logs, backups (if maintained), or past Discord announcements. Request broader deletion, access, or correction from the operator using the contact route below. Such requests may require reasonable identity verification and manual action. Retained information will be reviewed and removed when no longer necessary, subject to applicable legal requirements; no automatic deletion deadline or backup schedule is implemented. Past Discord messages must be removed separately by someone with permission to delete them.

## Contact and updates
For privacy questions or to arrange a private data request, [open a GitHub issue addressed to hf-keo](https://github.com/hf-keo/tts-birthday-bot/issues/new), or ask your server administrator to contact the operator. GitHub issues are public: request a private contact method first and do not publish birthdays, tokens, IDs linked to a private request, or other personal information there. GitHub processes issue submissions under its own privacy statement.

You may have additional access, correction, deletion, objection, or complaint rights under applicable law. Contact the operator to discuss a request; this policy does not limit those rights. Changes will be published on this page with an updated effective date. See also the [Terms of Service](https://github.com/hf-keo/tts-birthday-bot/blob/main/TERMS.md).
