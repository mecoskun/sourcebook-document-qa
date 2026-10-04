# Shared CPU hosting shortlist and benchmark plan

Checked 2026-10-03. User prefers US hosting. No account, server, payment, or subscription created. No hosted benchmark has run.

## Requirements

One private CPU model service for Sourcebook and the later transcript-only summarizer. Current compose limits: model 6 GB, API 2 GB, plus OS/runtime headroom. Target at least 12 GB RAM, x86-64, four usable CPU threads and 40 GB disk. Prefer 16–24 GB if affordable. Shared vCPU count does not guarantee inference speed. The USD 20–30 monthly budget remains a target.

## Official-source comparison

- **OVHcloud US VPS-3 (2027): first benchmark candidate.** 6 vCores, 12 GB RAM, 100 GB NVMe. Advertised from USD 12.32/month. The linked configurator selects `pricing=upfront12`: this is not a confirmed month-to-month quote. Verify US-region stock, month-to-month total, taxes, renewal and cancellation before ordering. IPv4 and basic daily backup are listed as included. Source: https://us.ovhcloud.com/vps/ . Configurator: https://us.ovhcloud.com/vps/configurator/?brick=VPS%2BModel%2B3&planCode=vps-2027-model3&pricing=upfront12&processor=+&storage=100__SSD__NVMe&vcore=6__vCore . The exact checkout configuration is not verified.
- **OVHcloud US VPS-4:** 8 vCores, 24 GB RAM, 200 GB NVMe, advertised from USD 23.37/month with the same annual-prepayment caveat. More memory headroom; benchmark before treating more cores as faster inference.
- **DigitalOcean Basic:** 8 vCPUs, 16 GiB RAM, USD 96/month listed, outside budget. Source: https://www.digitalocean.com/pricing/droplets .
- **Hetzner CX43 EU:** 8 vCPUs, 16 GB RAM. Official adjustment table lists USD 18.49/month excluding VAT and IPv4, but its public product page reports unavailable. EU location also conflicts with the US preference. Sources: https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/ and https://www.hetzner.com/cloud/cost-optimized/ .
- **netcup:** older search snippets show cheaper G12 prices, but the current official listing is G12.5. Do not use the old snippets for a purchase estimate. Current displayed 16 GB plan pricing is term-dependent and is not the first US benchmark candidate. Source: https://www.netcup.com/en/server/vps .

Prices are observations, not binding quotes. USD and EUR listings were not converted or mixed. Region, term, tax and availability must be confirmed at checkout.

## Benchmark procedure after account/server approval

1. Confirm a month-to-month US quote within the budget, without annual commitment or paid extras. User completes account/payment steps. Do not provision until the specific quote is accepted.
2. Use Ubuntu LTS x86-64, SSH key access and a firewall. Keep the model and API host ports private during testing; reach the API through an SSH tunnel. Do not connect the public Pages UI yet.
3. Clone the pinned app commit, prepare checksum-verified models, build Docker containers and verify health/readiness. Record CPU model, RAM, OS, Docker version, model digest and commit.
4. Run the existing pre-hosting, format and date suites on the host, recording outputs and cold/warm timings. Run only synthetic/public documents. Record container peak memory, host available memory, swap activity and OOM events with Docker/OS monitoring.
5. Repeat representative short and longer questions at different times of day to observe shared-CPU variation. Proposed demo targets: warm median <=20 seconds, p95 <=45 seconds, no OOM/restarts, and >=2 GB host memory headroom. These are acceptance targets, not measured results.
6. Check two simultaneous API requests: the current demo should handle one and return a clear busy response to the other. Verify isolation, expiry, upload caps and clean restart. Both apps will share one generation slot initially; combined usage limits are required when YouTube is added.
7. If suitable, keep the chosen server and proceed to HTTPS reverse proxy and GitHub Pages connection. If unsuitable, record the failure and arrange cancellation before renewal; do not silently upgrade the budget.

## Immediate next action

Confirm whether the user has an OVHcloud US account, then inspect a concrete month-to-month quote and US-region availability. The comparison and benchmark plan are ready; hosted performance remains unknown.
