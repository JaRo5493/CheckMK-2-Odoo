# CheckMK-2-Odoo Notification Script

## Getting started

Das notify_odoo.py Script in diesem Repository ermöglicht CheckMK direkt Tickets in Odoo zu erstellen. \
Dazu muss das Script unter der jeweiligen CheckMK Instanz "~/local/share/check_mk/notifications/notify_odoo.py" abgelegt werden.

Danach können die Einstellungen für das Script in CheckMK unter Setup -> Events -> Notifications konfiguriert werden.\
Die Parameter die dem Script mitgegeben werden müssen sind: \
#1 - Odoo URL (https://my.odoo.ch) \
#2 - Odoo Database Name (my) \
#3 - Odoo User UID (2) \
#4 - Odoo User API Token (whatevertoken) \
