from assistant.system.performance import (
    summarize_performance,
)


def test_performance_summary():
    records = [
        {
            "total_seconds":
                10.0,

            "marks": {
                "first_authoritative_sentence":
                    2.0,

                "first_audio_started":
                    4.0,
            },

            "spans": [
                {
                    "name":
                        "reasoning",

                    "seconds":
                        3.0,
                },
                {
                    "name":
                        "tts_total",

                    "seconds":
                        5.0,
                },
            ],
        },
        {
            "total_seconds":
                20.0,

            "marks": {
                "first_authoritative_sentence":
                    4.0,

                "first_audio_started":
                    6.0,
            },

            "spans": [
                {
                    "name":
                        "reasoning",

                    "seconds":
                        5.0,
                },
                {
                    "name":
                        "tts_total",

                    "seconds":
                        8.0,
                },
            ],
        },
    ]

    summary = (
        summarize_performance(
            records
        )
    )

    assert summary.request_count == 2
    assert summary.median_total_seconds == 15.0
    assert summary.median_time_to_first_sentence == 3.0
    assert summary.median_time_to_first_audio == 5.0
    assert summary.primary_bottleneck == "tts_total"
    assert summary.slow_request_count == 1
