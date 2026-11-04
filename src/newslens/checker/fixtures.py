"""NewsLens checker — Predefined offline demonstration fixtures.

Clean-room implementation. No external API calls are made.

Used exclusively in Offline Demo Mode to demonstrate the application interface,
evidence card formatting, stance labeling, and uncertainty/confidence handling
without requiring external API credentials (Tavily or Groq).

CRITICAL INVARIANT:
Demo fixtures must NEVER be passed off as live results or used as silent fallbacks
when live API calls fail. Every fixture is explicitly tagged with DEMO_FIXTURE_LABEL.
"""

from __future__ import annotations

from typing import Any

from newslens.checker.schema import Source, Verdict

DEMO_FIXTURE_LABEL: str = "DEMO / FIXTURE DATA — NOT A LIVE FACT CHECK"

# Sample claims available for quick selection in demo mode
DEMO_SAMPLE_CLAIMS: dict[str, str] = {
    "Great Wall of China (Refuted)": "The Great Wall of China is visible from space with the naked eye.",
    "Heliocentrism (Supported)": "The Earth revolves around the Sun.",
    "Bananas & Radiation (Misleading)": "Eating bananas exposes you to dangerous levels of nuclear radiation.",
}

# Pre-recorded fixtures
_FIXTURES: dict[str, tuple[list[dict[str, Any]], set[str], Verdict]] = {
    "The Great Wall of China is visible from space with the naked eye.": (
        [
            {
                "url": "https://www.nasa.gov/vision/space/workinginspace/great_wall.html",
                "title": "[DEMO FIXTURE] NASA - China's Wall Less Great in View from Orbit",
                "snippet": (
                    "Astronauts and orbital imagery confirm the Great Wall of China is not "
                    "discernible to the unaided human eye from low Earth orbit. The wall is narrow "
                    "and composed of materials that blend with the surrounding terrain."
                ),
            },
            {
                "url": "https://www.scientificamerican.com/article/is-chinas-great-wall-visible-from-space/",
                "title": "[DEMO FIXTURE] Scientific American - Is China's Great Wall Visible from Space?",
                "snippet": (
                    "It has become an established urban myth that the Great Wall is the only man-made "
                    "structure visible from space. In reality, without optical magnification, it is invisible."
                ),
            },
            {
                "url": "https://en.wikipedia.org/wiki/Great_Wall_of_China#Visibility_from_space",
                "title": "[DEMO FIXTURE] Wikipedia - Visibility of Great Wall from Orbit",
                "snippet": (
                    "Chinese astronaut Yang Liwei stated he could not see the Great Wall during his flight. "
                    "NASA has corroborated that it is barely visible only under very specific optical conditions."
                ),
            },
        ],
        {
            "https://www.nasa.gov/vision/space/workinginspace/great_wall.html",
            "https://www.scientificamerican.com/article/is-chinas-great-wall-visible-from-space/",
            "https://en.wikipedia.org/wiki/Great_Wall_of_China#Visibility_from_space",
        },
        Verdict(
            verdict="refuted",
            confidence="high",
            summary=(
                f"[{DEMO_FIXTURE_LABEL}] Multiple astronaut observations and orbital optical analyses "
                "confirm that the Great Wall of China cannot be seen from space with the naked human eye."
            ),
            reasoning=(
                "The Great Wall has a maximum width of only a few meters and is constructed from materials "
                "whose color matches the surrounding soil and mountains. Human visual acuity from orbit "
                "is insufficient to distinguish such narrow structures without high-powered lenses. "
                "Astronauts from NASA, ESA, and CNSA have confirmed its naked-eye invisibility."
            ),
            caveats=(
                f"[{DEMO_FIXTURE_LABEL}] Segments can be identified with high-resolution telephoto cameras, "
                "radar imagery, or under rare low-sun grazing light, but the popular claim of naked-eye visibility is false."
            ),
            sources=[
                Source(
                    url="https://www.nasa.gov/vision/space/workinginspace/great_wall.html",
                    title="[DEMO FIXTURE] NASA - China's Wall Less Great in View from Orbit",
                    stance="refutes",
                    snippet="Astronauts confirm the wall is not discernible to the unaided human eye from low Earth orbit.",
                ),
                Source(
                    url="https://www.scientificamerican.com/article/is-chinas-great-wall-visible-from-space/",
                    title="[DEMO FIXTURE] Scientific American - Is China's Great Wall Visible from Space?",
                    stance="refutes",
                    snippet="It has become an established urban myth; in reality, without magnification, it is invisible.",
                ),
            ],
        ),
    ),
    "The Earth revolves around the Sun.": (
        [
            {
                "url": "https://solarsystem.nasa.gov/solar-system/our-solar-system/in-depth/",
                "title": "[DEMO FIXTURE] NASA Solar System Exploration - Heliocentrism",
                "snippet": (
                    "The Earth and other planets orbit the Sun at the center of our solar system, "
                    "completing one revolution approximately every 365.25 days."
                ),
            },
            {
                "url": "https://en.wikipedia.org/wiki/Heliocentrism",
                "title": "[DEMO FIXTURE] Wikipedia - Heliocentric Model",
                "snippet": (
                    "Heliocentrism is the astronomical model in which the Earth and planets revolve "
                    "around the Sun. Supported by centuries of observational evidence from Galileo to modern astrophysics."
                ),
            },
        ],
        {
            "https://solarsystem.nasa.gov/solar-system/our-solar-system/in-depth/",
            "https://en.wikipedia.org/wiki/Heliocentrism",
        },
        Verdict(
            verdict="supported",
            confidence="high",
            summary=(
                f"[{DEMO_FIXTURE_LABEL}] The claim that the Earth revolves around the Sun is conclusively "
                "supported by fundamental astronomy, gravitational physics, and satellite telemetry."
            ),
            reasoning=(
                "Centuries of astronomical observation, celestial mechanics, stellar parallax measurements, "
                "and modern interplanetary spaceflight establish that the Earth follows an elliptical orbit around the Sun."
            ),
            caveats=(
                f"[{DEMO_FIXTURE_LABEL}] In gravitational physics both bodies technically orbit their common barycenter, "
                "which lies near or within the volume of the Sun."
            ),
            sources=[
                Source(
                    url="https://solarsystem.nasa.gov/solar-system/our-solar-system/in-depth/",
                    title="[DEMO FIXTURE] NASA Solar System Exploration - Heliocentrism",
                    stance="supports",
                    snippet="The Earth and other planets orbit the Sun at the center of our solar system.",
                ),
            ],
        ),
    ),
    "Eating bananas exposes you to dangerous levels of nuclear radiation.": (
        [
            {
                "url": "https://www.epa.gov/radtown/natural-radioactivity-food",
                "title": "[DEMO FIXTURE] EPA - Natural Radioactivity in Food",
                "snippet": (
                    "Bananas naturally contain potassium-40, a radioactive isotope. However, the radiation "
                    "dose from eating a banana is roughly 0.1 microsieverts—infinitesimally small and completely harmless."
                ),
            },
            {
                "url": "https://en.wikipedia.org/wiki/Banana_equivalent_dose",
                "title": "[DEMO FIXTURE] Wikipedia - Banana Equivalent Dose",
                "snippet": (
                    "The banana equivalent dose is an informal measurement used to explain radiation exposure. "
                    "A human body maintains homeostatic potassium levels; ingested potassium does not accumulate radiation."
                ),
            },
        ],
        {
            "https://www.epa.gov/radtown/natural-radioactivity-food",
            "https://en.wikipedia.org/wiki/Banana_equivalent_dose",
        },
        Verdict(
            verdict="misleading",
            confidence="high",
            summary=(
                f"[{DEMO_FIXTURE_LABEL}] While bananas naturally contain trace radioactive potassium-40, "
                "the radiation level is completely harmless and does not pose a health hazard."
            ),
            reasoning=(
                "The claim is technically based on the fact that bananas contain potassium-40. However, "
                "framing this as 'dangerous nuclear radiation' is misleading: normal human biology tightly regulates "
                "potassium levels, and a typical banana delivers a dose of ~0.1 µSv—less than 1% of standard daily background radiation."
            ),
            caveats=(
                f"[{DEMO_FIXTURE_LABEL}] You would need to consume millions of bananas at once for the radiation "
                "to cause harm, which is physically impossible."
            ),
            sources=[
                Source(
                    url="https://www.epa.gov/radtown/natural-radioactivity-food",
                    title="[DEMO FIXTURE] EPA - Natural Radioactivity in Food",
                    stance="refutes",
                    snippet="The radiation dose from eating a banana is roughly 0.1 microsieverts—completely harmless.",
                ),
            ],
        ),
    ),
}


def get_demo_fixture(claim: str) -> tuple[list[dict[str, Any]], set[str], Verdict]:
    """Retrieve demo fixture data for *claim*.

    If *claim* matches one of the pre-recorded fixture claims, returns that exact fixture.
    Otherwise, returns a generic fallback fixture clearly explaining that offline demo mode
    does not execute live web searches or LLM reasoning for arbitrary text.

    Guarantees:
        - NEVER makes network requests or imports API clients.
        - NEVER returns unlabelled data.
    """
    clean = " ".join(claim.strip().split())

    # Check for direct match among known fixtures
    for fixture_claim, fixture_data in _FIXTURES.items():
        if clean.lower() == fixture_claim.lower():
            return fixture_data

    # Generic fixture fallback for custom user inputs in demo mode
    fallback_url = "https://demo.newslens.internal/offline-notice"
    fallback_sources = [
        Source(
            url=fallback_url,
            title="[DEMO FIXTURE] NewsLens Offline Demonstration Notice",
            stance="unrelated",
            snippet=(
                "Offline Demo Mode active. No external web search or LLM reasoning was performed "
                "for this custom claim. Configure GROQ_API_KEY and TAVILY_API_KEY to run live verification."
            ),
        )
    ]
    fallback_allowed = {fallback_url}
    fallback_verdict = Verdict(
        verdict="unverifiable",
        confidence="low",
        summary=(
            f"[{DEMO_FIXTURE_LABEL}] Custom claim received in Offline Demo Mode. "
            "No live web search or external AI reasoning was executed."
        ),
        reasoning=(
            "The application is currently operating in Offline Demo Mode. Pre-recorded fixtures are "
            "available for the sample claims provided above. For arbitrary custom claims, real-time "
            "evidence retrieval requires switching to Live Search Mode with valid Groq and Tavily credentials."
        ),
        caveats=(
            f"[{DEMO_FIXTURE_LABEL}] This response is generated entirely from local demonstration "
            "templates. It does not reflect web search results or external evidence."
        ),
        sources=fallback_sources,
    )
    return (
        [
            {
                "url": fallback_url,
                "title": "[DEMO FIXTURE] NewsLens Offline Demonstration Notice",
                "snippet": "Offline Demo Mode active. Real APIs are disabled.",
            }
        ],
        fallback_allowed,
        fallback_verdict,
    )
