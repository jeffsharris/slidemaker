# Intake

Topic: LLM Latency
Aspect ratio: 16:9 (1536x1024)
Audience: Mixed technical depth, high-level, tech industry background

## Raw notes (verbatim capture)
- Two primary components of language model latency:
  1) Prompt processing time, often called time to first token (TTFT)
  2) Output token generation rate, called time between tokens (TBTT)
- First slide should illustrate that distinction.
- Most time for most models is spent generating each output token because an output token takes something like 100x more time to generate than an input token to process.
- Second slide: scatter plot with time between token latency on y-axis and tokens per minute per GPU on x-axis. Roughly linear pattern where as tokens per minute per GPU increases, time between tokens also increases.
- Third slide: explain why with a highway metaphor. As more cars try to enter the highway, it backs up and slows generation.
- Another slide: batch size concept. Smaller batch size means less wait per forward pass (green light flashes quickly). Larger batch size means more can enter simultaneously but each forward pass is slower to fill. Probably multiple slides for this.
- Slide: zoomed out global network of data centers. Two trade-offs controlling latency:
  1) Queuing inside the transformer
  2) Load balancer that spreads requests across clusters worldwide
- Transformer-side factors controlling latency:
  1) Model architecture: smaller models are faster than larger models
  2) Input vs output tokens are very different (input tokens about 100x more efficient)
  3) Cached input tokens are free (prompt prefix already seen is free)
- Another slide: prompt prefix is cheap, uncached input tokens are more expensive, output tokens most expensive.
- Longer requests are expensive for two reasons:
  1) Bigger requests are harder to fit into a single batch (like wider cars on a highway)
  2) Token cost increases slightly with length; quadratic growth adds up
- Slide titles should be short text on each slide (1-2 words). Basic text is allowed but should be minimal.
- Scatter plot trend is upward: more tokens/minute per GPU implies higher time between tokens.

Additional slides: how to make models faster (one strategy per slide)
1) Smaller models: show size vs speed, smaller is faster.
2) Model architecture: mixture of experts / sparsity lets model skip work by routing to specialized components.
3) Proxy models: speculate batches of tokens, validate in one pass if correct.

## Candidate slide sequence (draft)
1) TTFT vs TBTT: two phases of latency
2) Output token cost dominates (scatter plot)
3) Highway metaphor: more cars -> congestion -> slower tokens
4) Batch size tradeoff: ramp light mechanism
5) Global data center network: queue vs load balancing
6) Transformer-side latency factors (model size, input vs output, cached prefix)
7) Cost tiers: cached prefix vs uncached input vs output tokens
8) Long requests are expensive (batch fit + quadratic cost)
9) Smaller models are faster
10) Model architecture efficiency (MoE / sparsity)
11) Proxy models / speculative decoding

## Open questions
- Confirm or revise the visual style and color palette above.


Update: Split latency factors into separate slides (model size, input vs output, cached prefix).
Add tradeoff slide: capability vs cost vs latency.
Add speedup slides: add capacity, newer hardware.


Update: Terminology uses TBT (time between tokens). Added cover, metrics, latency budget, output dominates, context/KV growth, and speedups (quantize, KV cache, capacity, wafer-scale hardware).

Update: Reworked deck with deadpan corporate motif, strict text control, and more technical diagrams; removed latency budget/metrics slides; added request timing, batching, routing, KV, quantization, wafer-scale hardware.

Update: Reworked deck with deadpan corporate motif, strict text control, and more technical diagrams; added end-to-end latency slide and output dominance; removed p95.