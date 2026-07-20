---
title: "Fable 5 Transcription Kit"
description: "Upload images of manuscripts and receive a transcription — a prompt kit built and tested for Claude Fable 5."
publishDate: 2026-07-20
status: published
download: fable-5-transcription-kit.zip
promptFile: fable-5-transcription-prompt.txt
---

The Fable Transcription Kit allows you to upload images of manuscripts and receive a transcription. The Fable Kit was tested in a blind protocol where agents were given a manuscript page, some prompting, and asked to produce a transcription. Across 15 experimental runs that included five different hands ranging from legible to very challenging, the Fable Kit beat the current benchmark of a Character Error Rate (CER) under 5%. The experimental runs averaged a CER of 3.16%. All CERs were calculated by an independent review script, so the transcribing agent had no knowledge of its score. Likewise, the transcribing agent had no knowledge of the ‘correct’ transcription.

Currently, Fable is only available to Claude Pro, Max and Enterprise Subscribers, and via the API where you can purchase credits. During the experiment, the cost per transcription averaged $7.96 in API pricing with prompt caching.

If you use a model other than Fable, then you will not get the same results and will likely receive a transcription with a much higher CER. The next toolkit will be tailored to a model that does not require a subscription.

### 1) For subscribers

Once you’ve downloaded the toolkit, here’s how to use it if you have a Claude subscriber account or plan to purchase one:

1. Go to claude.ai.
2. Create a Claude Pro account if you do not have one.
3. Start a new chat, making sure that you’ve selected Fable as the model. Claude usually defaults to Sonnet.
4. Upload a copy of your manuscript image and paste the prompt from the kit.
5. Hit send and you’ll receive your transcription!

### 2) For purchasing Fable credits

Once you’ve downloaded the toolkit, here’s how to use it if you plan to use the toolkit by purchasing Fable credits:

1. Go to platform.claude.com.
2. Create an account by going to Billing and then purchasing pre-paid credits.
3. Open the Workbench from the Console’s navigation to start a new chat, making sure that you’ve selected Fable as the model. Claude usually defaults to Sonnet.
4. Upload a copy of your manuscript image and paste the prompt from the kit.
5. Hit send and you’ll receive your transcription!

Once you receive your transcription, you may notice that agents include the following:

- `[word?]` when the agent can see the word but isn’t certain of the reading
- `[b....es]` when the agent can make out a partially legible word, where the real letters are visible and the dots represent unknown letters
- `[...]` when nothing is traceable at all to the agent

These markers are a design feature to prevent hallucination—it’s better that an agent admits when it doesn’t know something—and are modeled after how human paleographers account for unknowns in their transcriptions. You may see more of these markers if your manuscript page is damaged, if the ink is too faded, or if the image is poor quality.
