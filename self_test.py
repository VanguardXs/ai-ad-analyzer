

import json
import os

import pandas as pd

import ad_core as ac


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class FakeClient:
    """Stands in for a real LLM client, returning schema-shaped fake JSON."""

    class chat:
        class completions:
            @staticmethod
            def create(model, temperature, messages, **kwargs):
                prompt = messages[0]["content"]
                if "DATA (winning ads" in prompt:
                    content = json.dumps({
                        "winning_patterns": {
                            "common_hooks": ["founder authenticity", "quiet-luxury visual flex"],
                            "common_angles": ["status-driven", "aspirational"],
                            "common_formats": ["founder VSL", "unboxing"],
                            "common_triggers": ["prestige", "exclusivity"],
                        },
                        "why_it_works": "These ads skip discount language and instead frame the "
                                        "product as proof of taste and success, which is what "
                                        "this audience actually buys.",
                        "audience_insights": {
                            "status_drivers": ["quiet, recognizable quality"],
                            "prestige_desires": ["effortless ownership", "white-glove service"],
                            "key_objections": ["is it really worth the price", "will it last"],
                        },
                        "new_ad_concepts": [
                            {
                                "concept_name": "The Quiet Flex",
                                "hook": "This is the piece that makes people ask where you got it.",
                                "angle": "status-driven",
                                "format": "founder VSL",
                                "script_outline": "1) cold open on the object 2) founder voiceover "
                                                   "on craftsmanship 3) reveal price frame 4) CTA",
                                "why_it_should_work": "Mirrors the founder-authenticity pattern "
                                                       "that already wins with this audience.",
                                "what_to_test": "founder voiceover vs no voiceover",
                            },
                            {
                                "concept_name": "White Glove Proof",
                                "hook": "You never touch a box. We make sure of that.",
                                "angle": "concierge experience",
                                "format": "service walkthrough",
                                "script_outline": "1) order 2) concierge call 3) delivery moment "
                                                   "4) CTA",
                                "why_it_should_work": "Leans on the seamless-experience desire "
                                                       "this audience consistently responds to.",
                                "what_to_test": "service-first hook vs product-first hook",
                            },
                            {
                                "concept_name": "Proof Over Price",
                                "hook": "We don't discount. We just don't have to.",
                                "angle": "anti-discount / quality",
                                "format": "UGC testimonial",
                                "script_outline": "1) callout 2) testimonial 3) close-up detail "
                                                   "4) CTA",
                                "why_it_should_work": "Directly counters the discount-seeking "
                                                       "objection this audience doesn't have.",
                                "what_to_test": "testimonial-led vs founder-led open",
                            },
                        ],
                        "testing_recommendations": [
                            "Test founder-led vs UGC-led opens on the same offer.",
                        ],
                    })
                else:
                    content = json.dumps({
                        "hook_style": {
                            "angle": "status-driven",
                            "why_it_grabs_them": "Opens on scarcity of taste, not price, which "
                                                  "signals it's for people who already know what "
                                                  "they want.",
                        },
                        "core_angle_mechanism": {
                            "main_message": "Quality you never have to think about twice.",
                            "must_have_positioning": "Framed as a mark of already having arrived, "
                                                      "not a way to get there.",
                        },
                        "objections_handled": ["durability", "is it really better quality"],
                        "visual_script_structure": {
                            "what_video_shows": "Close-up material and finish shots.",
                            "what_transcript_says": "Founder voiceover on why every detail was "
                                                     "chosen.",
                            "pacing_notes": "Slow open, quickens on the reveal.",
                        },
                        "psychological_triggers": ["exclusivity", "authority", "identity signaling"],
                    })
                return _FakeResponse(content)


def main():
    api_key = os.environ.get("LLM_API_KEY") or os.environ.get("GROQ_API_KEY")
    if api_key:
        client = ac.get_client(api_key)
        print("Using real LLM client (key found in environment).")
    else:
        client = FakeClient()
        print("No LLM_API_KEY/GROQ_API_KEY set -- using a mocked client for this self-test.")

    df = pd.read_csv("sample_ads.csv")
    metrics_df = ac.compute_metrics(df)
    winners = ac.pick_winners(metrics_df, metric="ROAS", top_n=3, min_spend=1000.0)
    winner_names = list(winners["ad_name"])
    assert winner_names, "No winners selected -- check pick_winners/min_spend."

    analyses = {}
    for _, row in winners.iterrows():
        name = row["ad_name"]
        analyses[name] = ac.analyze_ad(str(row.get("transcript", "")), client)
        assert "hook_style" in analyses[name]
        assert "core_angle_mechanism" in analyses[name]
        assert "visual_script_structure" in analyses[name]

    payload = []
    for name in winner_names:
        row = metrics_df[metrics_df["ad_name"] == name].iloc[0]
        payload.append({
            "ad_name": name,
            "metrics": {"ROAS": float(row["ROAS"]), "CTR": float(row["CTR"]),
                        "CPA": float(row["CPA"]), "CVR": float(row["CVR"]),
                        "spend": float(row["spend"])},
            "creative_breakdown": analyses[name],
        })
    insights = ac.synthesize_insights(payload, client)
    assert len(insights.get("new_ad_concepts", [])) >= 3, "Expected at least 3 new ad concepts."
    assert "status_drivers" in insights.get("audience_insights", {})

    excel_bytes = ac.build_excel_bytes(metrics_df, winner_names, analyses, insights)
    assert len(excel_bytes) > 0

    report_md = ac.build_markdown_report(metrics_df, winner_names, analyses, insights, "ROAS")
    assert "Hook angle" in report_md
    assert "Status drivers" in report_md

    print(f"Winners ({len(winner_names)}): {winner_names}")
    print(f"Excel bytes: {len(excel_bytes)}")
    print(f"Report length: {len(report_md)} chars")
    print("Self-test passed: pipeline runs end to end without errors.")


if __name__ == "__main__":
    main()
