# Technical Proposal: Distributed Audio Streaming Platform with Integrated Live Chat

## TL;DR

- **Build a single CMAF-based media pipeline that packages once and serves HLS/LL-HLS to every client**, deliver it over **Cloudflare R2 (zero-egress) + CDN** to neutralize the dominant cost driver, and pair it with an **Elixir/Phoenix live-chat tier**. For a 5–15 engineer team, **buy the media pipeline and DRM early, build the chat tier, and never build a CDN or transcoding SaaS from scratch in Phase 1.**
- **Use native mobile players (ExoPlayer/Media3 on Android, AVPlayer/AVAudioSession on iOS) with a Kotlin Multiplatform shared logic core** — cross-platform frameworks do not adequately handle the background-playback, lock-screen, and encrypted-offline requirements that define a serious audio product; on the web, Managed Media Source (iOS 17.1+) now lets hls.js/Shaka run everywhere including iOS Safari.
- **Egress is the whole ballgame:** at 128 kbps, 100,000 concurrent listeners consume ~5.7 TB/hour. Choosing R2/Cloudflare over AWS/GCP egress ($0/GB vs ~$0.085–0.12/GB) can cut delivery cost by an order of magnitude and is worth potentially six figures/year at scale.

## Key Findings

1. 1. **A single CMAF (fMP4) encode serves both live and on-demand across all platforms.** One set of segments feeds an HLS manifest (Safari/iOS, everywhere) and a DASH manifest (Android/smart TVs) — eliminating parallel pipelines. CMAF chunked transfer reaches ~3–6s glass-to-glass; LL-HLS partial segments reach 2–4s at CDN scale.
2. 2. **WebRTC egress (WHEP) is not yet production-safe as a core dependency.** WHIP ingest is now a real standard — RFC 9725, published March 2025 by S. Garcia Murillo (Millicast) and A. Gouaillard (CoSMo Software) via the IETF WISH working group ("This is an Internet Standards Track document… approved for publication by the [ietf][ref-01] IESG," updating RFC 8840 and 8842). [ietf][ref-01] WHEP, however, remains an expired IETF draft (draft-ietf-wish-whep-03) as of 2026, not an RFC. Treat WebRTC delivery as directional only.
3. 3. **Elixir/Phoenix is the standout choice for the chat fan-out tier.** The official Phoenix Framework blog "The Road to 2 Million Websocket Connections in Phoenix" (2015) documented 2 million concurrent WebSocket connections on a single 40-core/128GB box ("2 million clients, limited by ulimit"); [GitHub][ref-02] a later DigitalOcean 64GB/20-core reproduction reached 2.3M, limited by memory. [GitHub][ref-03] Fan-out amplification — not connection count — is what breaks first at 100K-viewer scale.
4. 4. **Egress cost dwarfs everything else and is the single most important architectural decision.** A 128 kbps stream uses ~57 MB per listener-hour. Per-GB egress ranges from $0 (Cloudflare R2) and ~$0.005–0.01 (Bunny) to ~$0.085 (CloudFront) and ~$0.12 (GCP, Fastly first tier).
5. 5. **DRM is rarely justified for audio.** AES-128/SAMPLE-AES HLS encryption with token-protected keys and signed URLs is a defensible baseline; full Widevine+FairPlay is warranted only when a music-label licensing contract's content-protection annex requires hardware-backed DRM.

## Details

### Goals and Non-Goals

**Goals:** sub-3s glass-to-glass live latency where affordable; universal playback (Safari/iOS, Chrome, Firefox, Android); on-demand catalog with adaptive audio; live chat synchronized to playback; a scaling path from thousands to millions of concurrent listeners; multi-region readiness.

**Non-Goals (Phase 1):** sub-500ms interactive WebRTC audio at scale; full studio-grade multi-DRM; building our own CDN; building our own transcoding SaaS; real-time recommendations ML; Kubernetes.

### Architecture Overview

The system decomposes into seven planes:

1. **Ingest tier** for live broadcasters
2. **Media pipeline** (transcode + CMAF package)
3. **Origin + CDN** for segment delivery
4. **Client apps** (web, iOS, Android)
5. **Chat subsystem** (Phoenix)
6. **Backend services** (auth/identity, catalog/metadata, playback/licensing, live session management, chat, recommendations, analytics/telemetry, billing)
7. **Data stores** (Postgres, Redis, ClickHouse, object storage, search)

Content flows left-to-right: broadcaster → ingest → transcode → CMAF package → origin (R2/S3) → CDN → player. Chat and QoE telemetry run as parallel real-time paths, joined to playback via program-time timestamps.

### Media Pipeline

**Ingest (live).** Use **SRT** as the primary broadcaster contribution protocol, with **RTMP** retained for legacy encoders/OBS. RTMP runs on TCP and stalls on lossy links (typically 3–5s latency); SRT runs on UDP with active packet recovery and achieves sub-2s, [VideoSDK][ref-04] and since SRT 1.5 its connection bonding closed the prior gap with RIST. [5centsCDN][ref-05] Support **RIST** only if a broadcast-compliance customer specifically requires DTLS certificate-based auth. Support **WHIP** (RFC 9725) for browser-based broadcasters needing sub-second contribution — OBS Studio ships built-in WHIP.

**Transcode + package.** Use **FFmpeg-based containerized transcoding workers** driven by a job queue for on-demand catalog, running on spot/preemptible instances; run a continuous transcode/packager for live. Emit a **single CMAF (fMP4) segment set** feeding both HLS and DASH manifests. For a team this size, **do not build the pipeline in Phase 1** — start on **Mux** or **Cloudflare Stream** and cut over to self-hosted FFmpeg only past the cost crossover.

**Codecs.**

- **AAC-LC** — universal baseline; every browser, phone, and TV decodes it in hardware.
- **HE-AAC v1/v2** — low-bitrate rungs.
- **xHE-AAC** — a second mobile rendition; adapts smoothly from ~12 kbit/s upward with built-in loudness/DRC; supported on iOS 13+, Android Pie+, Windows 11, and decoded by Chrome inside HLS.
- **Opus** — for WebRTC paths. Note the industry is consolidating on AAC-HLS: per SoundCloud's Backstage Blog (Sept 15, 2025), "We plan to remove Progressive HTTP, HLS MP3 and HLS Opus transcodings from our APIs on December 31, 2025… [SoundCloud Developers][ref-06] we're moving to AAC-based HLS streams" (preferring hls\_aac\_160\_url , fallback hls\_aac\_96\_url ).
- **FLAC/ALAC** — lossless tier only if a premium product demands it.

**Bitrate ladder.** Audio ladders are shallow. Sensible rungs: **96 / 128 / 160–256 kbps AAC** for music; **64 kbps HE-AAC or xHE-AAC** for speech/podcast; optional lossless ~1 Mbps. Adaptive bitrate matters far less for audio than video: a single well-chosen 128 kbps rendition plus one low rung covers most listeners. ABR earns its complexity mainly on variable mobile networks and for lossless tiers.

### CDN and Delivery — the Cost Center

Egress dominates the bill. At 128 kbps (~57 MB/listener-hour), **100,000 concurrent listeners for one hour ≈ 5.7 TB**; monthly totals scale with average concurrency, not peak, so model the concurrency curve carefully.

Per-GB egress:

- **Cloudflare R2: $0 egress**, storage ~$0.015/GB-month.
- **Bunny: ~$0.005–0.01/GB.**
- **AWS CloudFront: ~$0.085/GB; GCP: ~$0.12/GB; Fastly: ~$0.12/GB first tier.**
- Cloudflare CDN bandwidth is unmetered (plan-fee model).

**Recommendation:** store masters and segments on **Cloudflare R2** and deliver via **Cloudflare CDN** (or Bunny for raw per-GB at very high volume), avoiding AWS/GCP egress entirely. Use **origin shielding**, immutable segment names for high cache-hit ratios, and **signed URLs / token auth** for access control. Adopt **multi-CDN** only at Phase 3.

**Build vs buy crossover.** Managed platforms (Cloudflare Stream at ~$1 per 1,000 delivery-minutes; Mux at ~$0.025/min delivery plus encoding) are cheapest until volume is large; above ~500,000 delivery-minutes/month, offloading delivery to a dedicated CDN becomes worth evaluating. [BlazingCDN][ref-07] Icecast/SHOUTcast legacy servers still work for simple internet-radio single-bitrate streams but offer no ABR, no CDN-native packaging, and no modern player integration — not recommended for a new build.

### Live Chat Subsystem

**Runtime.** The recommended choice is **Elixir/Phoenix Channels** on the BEAM. Benchmarks report ~2M connections per node; lightweight processes support per-client backpressure, [Medium][ref-08] presence and graceful changes in cluster topology. This component is worth developing in-house.

**Pub/sub backbone.** Start with **Phoenix.PubSub backed by Redis**. If durability/replay becomes necessary, introduce **Redis Streams** (sub-ms p99, good to ~10K msg/s) or **NATS JetStream** (Kubernetes-native, ~820K msg/s). [DEV Community][ref-09] **Kafka** should serve analytics, not chat: it is excessive for fan-out and brings considerable operational overhead even in KRaft single-binary mode.

**Build vs buy.** The available managed options and prices are:

- **Ably** — consumption pricing confirmed from official docs: "Messages are charged at $2.50 per million messages consumed… [Ably][ref-10] as low as $0.50 per million," connections "$1.00 for every million minutes of activity"; [Ably][ref-10] free plan "6M messages / month, 200 concurrent connections, 500 messages / second." Pro tier ($399/mo) caps at 50,000 concurrent; 100K+ requires Enterprise (custom).
- **Cloudflare Durable Objects** — WebSocket-native; Workers Paid minimum $5/mo; requests +$0.15/million (WebSocket incoming messages billed at a 20:1 ratio); duration +$12.50/million GB-s. The **Hibernation API** means "Durable Objects that are idle and eligible for hibernation are not billed for duration," [cloudflare][ref-11] dramatically cutting idle cost for sparse-message rooms.
- **Stream (getstream.io) Chat** — MAU-based; free "Maker" tier; paid tiers start ~$399–$499/mo (exact figures require a sales quote).
- **PubNub** — MAU-based, no per-message fees; Starter $98/mo includes 1,000 MAU.
- **Centrifugo** — open-source Go server (MIT), self-hosted; benchmarked at 1M connections. [Centrifugo][ref-12] Cost = your VMs only.

For a quick launch, use a managed provider in Phase 1. Switch to self-hosted Phoenix when fan-out message volume makes per-message charges painful.

**Scaling math — the first constraint.** Fan-out amplification is the critical load in a 100K-viewer room: a single inbound message generates 100K outbound deliveries. With 10 inbound msg/sec, the result is 1M outbound msg/sec. **Egress bandwidth and per-connection serialization at the fan-out nodes** saturate before raw connection capacity. Mitigations include sharding rooms, batching/coalescing messages, applying per-user and per-IP rate limits, and sampling/aggregating the busiest rooms so that clients receive a representative subset.

**Audio/chat synchronization.** For **on-demand** playback, retain timestamped comments keyed to media position. For **live** playback, varying buffer depths mean that a message sent “now” reaches listeners separated by 3–30s in the stream. Timestamp chat using the stream's program time ( EXT-X-PROGRAM-DATE-TIME ), with optional delivery delay to align with each client's playback position. This drift deserves an explicit solution.

**Moderation, ordering, history.** Support per-room ordering, presence, durable-store history/backfill, rate limiting, spam/abuse handling and a moderation queue.

### Client Applications

**Browser.** Use **hls.js** (and/or **Shaka Player**) over **Media Source Extensions**. Critically, per WebKit's official blog "WebKit Features in Safari 17.1" (Nov 2023), "Safari 17.1 now brings the new Managed Media Source API to iPhone" [WebKit][ref-13] (originally shipped in Safari 17.0 for iPad and Mac); hls.js support landed in v1.5 (2024) and Shaka Player since 4.10. This eliminates the long-standing Safari-specific branch — the same JS player now runs on iOS. On native-HLS Safari paths, the <video src=m3u8> /AVPlayer route remains. Add **Web Audio API** for visualizations, **Media Session API** for lock-screen/hardware controls, and **Service Workers** for caching.

**Mobile — native players, not cross-platform.** Audio apps have heavy background-playback and OS-integration requirements (AVAudioSession/AVPlayer on iOS; ExoPlayer/Media3 on Android; lock-screen, notifications, offline/encrypted downloads, battery/network handling) that stress cross-platform frameworks. Use **ExoPlayer/Media3** on Android and **AVPlayer/AVAudioSession** on iOS directly. [Variant Systems][ref-14]

**Code sharing.** For non-player logic, share via **Kotlin Multiplatform (KMP)**. Per JetBrains' official case studies, "Netflix uses KMP to share logic for their mobile studio apps," [Kotlin][ref-15] Cash App transitioned from shared JavaScript to KMP in 2018, Philips uses KMP in its HealthSuite Digital Platform mobile SDK, [Kotlin][ref-16] and McDonald's KMP powers 6.5 million monthly purchases. [Kmpship][ref-17] The recommended strategy: shared TypeScript core for web + KMP for mobile business logic, with native players and native UI at the edges. Flutter/React Native are acceptable for surrounding UI but not for the audio-playback layer of a serious audio product.

### Backend Services and Data

**Languages.**

- **Go** for most services (catalog, playback, API gateway) — operational simplicity, performance, easy hiring.
- **Elixir** for the chat tier specifically.
- **Rust** only for hot-path media components if profiling justifies it.
- **Node/TypeScript** acceptable for BFFs.

**API layer.** **REST + OpenAPI** as the public/partner contract, **GraphQL as a BFF** for divergent web/mobile data needs, and **gRPC/Connect** for internal service-to-service (3–10x throughput over JSON). [APIScout][ref-18] Don't introduce gRPC until internal service count grows; don't build BFFs prematurely — start with one API and split only when client needs genuinely diverge.

**Data stores.**

- **PostgreSQL** — catalog/relational source of truth.
- **Redis** — hot state, presence, chat pub/sub.
- **ClickHouse** — playback/QoE telemetry at billion-row scale (the Sony LIV pattern: client SDKs → stream pipeline → ClickHouse for startup latency, buffering, device telemetry).
- **Object storage** — R2/S3 for masters and derivatives, with lifecycle policies moving cold masters to archival tiers.
- **Search** — Typesense or Meilisearch for catalog search (OpenSearch only if scale demands).

### Cross-Cutting Concerns

**AuthN/AuthZ.** OIDC + JWT with short-lived access tokens and refresh tokens (critical for long-lived mobile sessions), **signed playback tokens** per session, and device limits enforced at the licensing service.

**Content protection.** For most audio, **DRM is not justified**. Use **AES-128 / SAMPLE-AES HLS encryption with token-protected key delivery + signed URLs**. Escalate to **Widevine + FairPlay** only if a music-label content-protection annex requires hardware-backed DRM. FairPlay is the only DRM on Apple surfaces; [Gumlet][ref-19] a single CBCS/CMAF package can satisfy both FairPlay and Widevine, avoiding dual packaging. [Gumlet][ref-19]

**Observability.** **OpenTelemetry** end-to-end; a client-side QoE SDK capturing rebuffer ratio, startup time, bitrate switches, and playback failure rate; ClickHouse for event storage; standard metrics/log aggregation.

**Deployment.** Start on **managed containers (Cloud Run or ECS/Fargate)** — do not stand up Kubernetes in Phase 1. **Terraform** for IaC; standard CI/CD with progressive delivery (canary). Move to **Kubernetes** only when service count and team maturity justify it (Phase 2/3).

**Multi-region.** The CDN is already global on day one. Then add **Postgres read replicas**, then full regional compute deployments — in that order, only as latency/availability requires.

**Licensing/royalty reporting.** If this is a licensed music catalog, play-count reporting, territory restrictions, and an **immutable, event-sourced royalty ledger** (raw qualifying plays + rights-metadata version + deal terms, append-only, reconstructable years later for audit) are real engineering obligations driven by audit clauses. Budget for it and get legal input early.

### Scaling Roadmap

**Phase 1 — thousands of concurrent.** Managed media (Mux/Cloudflare Stream), R2 storage + Cloudflare CDN, managed chat OR a single Phoenix node, Postgres + Redis, Cloud Run/Fargate, single region. **Do NOT prematurely build** transcoding, Kubernetes, multi-CDN, DRM, or Kafka. *Trigger to Phase 2:* delivery-minutes or chat message volume make managed pricing painful, or sustained concurrency in the tens of thousands.

**Phase 2 — tens of thousands → low hundreds of thousands.** Self-hosted FFmpeg transcoding on spot; self-hosted Phoenix chat cluster with Redis/NATS backbone; ClickHouse analytics; event backbone appears; Postgres read replicas; possibly Kubernetes. *Trigger to Phase 3:* multi-region latency/availability needs, single-CDN risk, or >500K delivery-minutes/month.

**Phase 3 — hundreds of thousands → millions, multi-region.** Multi-CDN with steering; regional compute; sharded chat; full observability; multi-region data replication.

### Cost Model (order-of-magnitude)

- **Phase 1:** managed media + R2/CDN + small compute → low thousands $/month.
- **Phase 2:** self-hosted transcode + chat cluster + ClickHouse → tens of thousands $/month, egress-dominated but blunted by R2/Cloudflare.
- **Phase 3:** dominated by egress and multi-region compute; the R2/Cloudflare zero-egress decision is worth potentially hundreds of thousands/year versus AWS/GCP egress at scale.

*Chat cost illustration:* Ably at $2.50/M messages makes a high-fan-out 100K room expensive fast (fan-out bills every outbound message), which is precisely why self-hosting Phoenix becomes attractive at scale — a single large VM (~$500–1,500/month) can hold 1–2M connections.

### Build vs Buy Decisions

- **Media transcode/package:** BUY (Mux/Cloudflare Stream) in Phase 1; BUILD (FFmpeg) at scale.
- **CDN:** BUY always (Cloudflare/Bunny). Never build.
- **Chat runtime:** BUY managed in Phase 1; BUILD (Phoenix) at scale.
- **DRM license server:** BUY if ever needed. Never build.
- **Object storage:** BUY (R2).
- **Analytics store:** BUILD on ClickHouse (or ClickHouse Cloud).
- **Auth:** BUY an OIDC provider initially; revisit.

## Recommendations

**Immediately (Phase 1 build order):**

1. 1. Stand up **Cloudflare R2 + CDN** as the storage/delivery backbone before anything else — this locks in the zero-egress cost posture that determines the platform's economics.
2. 2. Ship on **Mux or Cloudflare Stream** for transcoding/packaging; do not write FFmpeg pipelines yet.
3. 3. Implement clients: web on **hls.js over MSE/Managed Media Source**; mobile with **native ExoPlayer/Media3 and AVPlayer**, sharing logic via **KMP**.
4. 4. Launch chat on a **managed provider** (or a single Phoenix node if the team has Elixir skills) with Redis pub/sub.
5. 5. Protect content with **AES-128/SAMPLE-AES + signed URLs**; skip DRM.
6. 6. Deploy on **Cloud Run/Fargate** with **Terraform**; run Go services + Postgres + Redis in a single region.

**Trigger-based escalations:**

- **When delivery > ~500K minutes/month or managed media billing exceeds self-host + 0.5–1 FTE:** move transcoding to **self-hosted FFmpeg on spot instances**.
- **When chat message volume makes managed per-message pricing painful:** stand up a **self-hosted Phoenix cluster** with NATS/Redis Streams.
- **When a licensing contract mandates it:** add **Widevine + FairPlay** via a bought DRM service and CBCS/CMAF packaging.
- **When p95 latency in a second region degrades or single-CDN risk is unacceptable:** add **Postgres read replicas**, then **multi-CDN steering**, then **regional compute** — in that order.

**Benchmarks that should change the plan:** sustained concurrency crossing ~10K (Ably Pro cap) or ~50K; delivery crossing ~500K minutes/month; chat fan-out approaching ~1M outbound msg/sec per room (shard sooner); any music-label content-protection annex (adds DRM + royalty-ledger scope).

## Caveats

- **Egress modeling is continuous, not one-time.** The 5.7 TB/hour-per-100K figure assumes 128 kbps and full occupancy; real bills depend on the average concurrency curve, which is currently unknown and should be instrumented from day one.
- **WHEP is still an IETF draft (not an RFC) as of 2026.** Do not make WebRTC audio egress a Phase 1 dependency; several vendors ship it, but it tracks a moving target.
- **Managed pricing figures shift.** Stream Chat's starting tier is quoted inconsistently across sources ($399 vs $499/mo) because all paid tiers route to sales; confirm by quote. Cloudflare's own hibernation cost example is disputed in a Cloudflare GitHub issue as possibly miscalculated — validate with a load test before committing.
- **Self-host chat benchmarks measure idle connection capacity, not message throughput.** The ~2M-connections-per-node figures are connection-holding benchmarks; heavy broadcast workloads need substantially more headroom, and the widely cited "$1,500/month machine" dates to a 2015 test (equivalent hardware is cheaper today).
- **Licensing/royalty obligations can dominate engineering scope** for a music catalog and require early legal input; they are outside the pure-infrastructure estimates above.
- **Open questions that drive concrete decisions:** the exact concurrency curve, the live-vs-on-demand traffic mix, and premium/lossless demand — all feed directly into ladder design, DRM decisions, and the Phase 2/3 triggers.

## Appendix: Technology Decision Table

| Area | Choice | Alternatives considered | One-line rationale |
| --- | --- | --- | --- |
| Live ingest | SRT (+RTMP compat, WHIP for browser) | RTMP-only, RIST | UDP recovery, sub-2s, bonding; RTMP for legacy; RIST only for DTLS-compliance needs |
| Packaging | CMAF (HLS + DASH) | Separate HLS/DASH pipelines | One encode, two manifests, all platforms |
| Delivery latency | LL-HLS / CMAF chunked | WebRTC egress (WHEP) | CDN-scale to 2–4s; WHEP not yet RFC |
| Baseline codec | AAC-LC | MP3, Opus-only | Universal hardware decode |
| Mobile codec rung | xHE-AAC | HE-AAC only | Smooth low-bitrate + loudness/DRC |
| Storage + CDN | Cloudflare R2 + CDN | AWS S3+CloudFront, GCP | Zero egress kills the dominant cost |
| Managed media (P1) | Mux / Cloudflare Stream | Self-host FFmpeg | Ship fast; crossover ~500K delivery-min/mo |
| Chat runtime | Elixir/Phoenix | Node, Go, managed | BEAM fan-out, ~2M conns/node |
| Chat backbone | Phoenix.PubSub + Redis → NATS | Kafka | Kafka over-engineered for fan-out |
| Web player | hls.js / Shaka on MSE/MMS | Native-only | Managed Media Source enables iOS Safari cross-platform |
| Mobile players | Native ExoPlayer/AVPlayer | Flutter/RN player | Background audio + OS integration |
| Mobile code share | Kotlin Multiplatform | Flutter, RN | Share logic, keep native players/UI |
| Primary backend lang | Go | Node, Rust, JVM | Simplicity + performance + hiring |
| API | REST + GraphQL BFF + gRPC internal | Single style | Right protocol per boundary |
| Analytics store | ClickHouse | Postgres, BigQuery | Billion-row QoE telemetry |
| Content protection | AES-128/SAMPLE-AES + signed URLs | Full multi-DRM | DRM rarely justified for audio |
| Orchestration (P1) | Cloud Run / Fargate | Kubernetes | Avoid premature k8s ops burden |
| Event backbone | None (P1) → NATS/Kafka (P2) | Kafka from day one | Add only when multiple consumers need it |

[ref-01]: <https://datatracker.ietf.org/doc/html/rfc9725>
[ref-02]: <https://github.com/phoenixframework/phoenix_site/blob/master/docs/blog/the-road-to-2-million-websocket-connections.html>
[ref-03]: <https://github.com/dsander/phoenix-connection-benchmark>
[ref-04]: <https://www.videosdk.live/developer-hub/rtmp/srt-vs-rtmp>
[ref-05]: <https://www.5centscdn.net/blog/rist-vs-srt/>
[ref-06]: <https://developers.soundcloud.com/blog/api-streaming-urls/>
[ref-07]: <https://blog.blazingcdn.com/en-us/cloudflare-streaming-pricing-2025-breakdown-live-vod>
[ref-08]: <https://medium.com/@connect.hashblock/elixir-on-beam-millions-of-websockets-no-sweat-739e4dd0de93>
[ref-09]: <https://dev.to/young_gao/real-time-event-streaming-kafka-vs-redis-streams-vs-nats-in-2026-34o1>
[ref-10]: <https://ably.com/docs/platform/pricing>
[ref-11]: <https://developers.cloudflare.com/durable-objects/platform/pricing>
[ref-12]: <https://centrifugal.dev/>
[ref-13]: <https://webkit.org/blog/14735/webkit-features-in-safari-17-1/>
[ref-14]: <https://variantsystems.io/industries/media-entertainment/react-native/>
[ref-15]: <https://kotlinlang.org/case-studies/>
[ref-16]: <https://kotlinlang.org/docs/multiplatform/use-cases-examples.html>
[ref-17]: <https://www.kmpship.app/blog/big-companies-kotlin-multiplatform-2025>
[ref-18]: <https://apiscout.dev/guides/rest-vs-graphql-vs-grpc-apis-2026>
[ref-19]: <https://www.gumlet.com/learn/fairplay-vs-widevine/>
