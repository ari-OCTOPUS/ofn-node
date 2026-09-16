# Board2 OFN gate CHG receipt
Auth: OCTOPUS-BOARD2-OFN-GATES-20260822
Host: DietPi 192.168.0.138
File: /home/ari/.config/ofn/node.env
Backup: /home/ari/.config/ofn/node.env.bak-gates-20260822-184609

## BEFORE
OFN_EXTRA_CLOSED_GATES=wire_outbound,live_email_send,live_publish,live_sms,live_dm,tender_submit,vendor_submit,portal_submit,terms_acceptance,fee_payment,auto_payment,auto_scrape,auto_post,auto_dm,auto_email

## AFTER
OFN_EXTRA_CLOSED_GATES=wire_outbound,live_sms,live_dm,tender_submit,vendor_submit,portal_submit,terms_acceptance,auto_scrape,auto_post,auto_dm,auto_email

## DROPPED only
- fee_payment
- auto_payment
- live_email_send
- live_publish

## Untouched
- All other closed gates left
- OFN_WIRE_OUTBOUND=0
- webhook_verify noop_until_vendor (unchanged)
- Phase-3 CONTROL_URL not modified

## Runtime
- sudo systemctl restart ofn.service → active, new PID, legs /healthz 8791–8794 = 200
