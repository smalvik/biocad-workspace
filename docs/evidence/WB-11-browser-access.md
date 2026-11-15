# WB-11 browser access incident — issue #21, 2026-11-15

**Status: monitoring; user reports browser access restored, no remediation applied.**
The latest instruction is to continue WB-06. No alternate ingress/DNS/cloud resource
was created. This user observation does not establish the cause or prove a permanent fix.

Historical diagnosis:
User reports `ERR_CONNECTION_RESET` for https://biocad.smalvik.dev.
This is not marked fixed or released. Branch `fix/wb-11-browser-access` starts from
develop b98a9a3 and carries only WB-05 post-release evidence (dc8bd17).

## Actual observations

- Authoritative DNS is Timeweb; the app's A record resolves to expected origin
  185.95.231.196. No app AAAA address was found.
- Direct connection from the workstation establishes TCP 443 in ~0.12–0.14 s,
  then strict TLS handshake times out. Another existing hostname on the same IP
  behaves the same. SSH banner is received, but key exchange times out/EOFs.
- AmneziaVPN is active, while the origin server IP uses the Wi-Fi route outside
  the tunnel. No global route/VPN/browser settings were modified.
- Simultaneous comparison to the **same IP/hostname**, with strict certificate
  validation: direct path timed out after 10.33 s; per-socket VPN path negotiated
  TLS 1.3 and returned HTTP 200 / bddba67 / 1.2.0 in **0.78 s**.
  [Actual comparison](../../artifacts/browser-access-path-comparison.json).
- SSH through the same per-socket VPN path succeeded with the original pinned host
  key and dedicated BIOCAD key; identity verification was not bypassed. Read-only
  server check returned HTTPS 200 / correct source. Available memory ~4.68 GB,
  conntrack 147/262144, proxy CPU 0.06%; no overload indication in this sample.
  Only one public IPv4, no global IPv6 address found.
- An ephemeral **loopback-only**, single-host CONNECT relay selected the VPN path
  per outgoing socket; it forwarded encrypted TLS without decrypting traffic.
  The exact v1.2.0 browser image opened the real public URL with normal certificate
  checks: **desktop/mobile form + own-list previews 2 passed, zero attempted booking
  writes, launcher exit 0**. [Metadata](../../artifacts/WB-11-browser-access/vpn-preview/run.json),
  [log](../../artifacts/WB-11-browser-preview.log). This proves access through the
  VPN route; it is not proof of direct public access or a permanent public fix.

The exact cause on the direct path (provider/filtering/MTU/other transport behavior)
is **not established**. Do not call the application fixed, blame a specific ISP,
or restart shared infrastructure based on these observations.

## Concrete public ingress requirements

Chosen direction requested by user: public browser access without client settings.

1. A separate reachable public ingress IP, preferably on a separate server/network,
   or a managed HTTPS proxy/CDN. First verify its direct accessibility from the
   affected network; another address alone is not an availability guarantee.
2. SSH/admin access to that proxy host, or provider access for a managed proxy.
   Secrets via local env/authorized key paths, never chat or git.
3. Control of **only biocad.smalvik.dev** DNS in Timeweb. A record for a VPS edge,
   or provider-required CNAME for a managed proxy. Existing other records stay intact.
4. Trusted automatic frontend TLS and encrypted, certificate-verified origin
   connection. Plan certificate renewal on both hops before switching DNS.
5. Validate the prepared proxy before cutover; then DNS, external browser login/map/
   form preview and preservation checks, with the old DNS target available for rollback.

Topology: browser -> new HTTPS ingress -> current BIOCAD server. Booking data and
application containers stay on the current host. No new cloud resource, public IP,
DNS change, firewall change or shared-proxy restart has been performed.
No DNS-provider credential is currently configured in local env.

Primary references: [Windows per-socket IPv4 interface selection](https://learn.microsoft.com/en-us/windows/win32/winsock/ipproto-ip-socket-options),
[Timeweb DNS editing](https://timeweb.com/ru/docs/domeny/resursnye-zapisi-domena-dns-zapisi/nastrojka-dns-zapisej/),
[certificate-verified HTTPS reverse proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy).

Commands actually used: strict Python socket/TLS probes, Resolve-DnsName,
Find-NetRoute/Get-NetIPInterface/Get-NetIPAddress (read-only), SSH connectivity,
per-socket compare_network_paths.py and server_ops_vpn.py, diagnostic local relay,
and browser_route_preview.py through run_logged.py. Failed direct attempts are kept.
