export type SeoFaqItem = {
  question: string
  answer: string
}

export type SeoExampleItem = {
  title: string
  body: string
}

export type SeoLinkItem = {
  href: string
  label: string
  description: string
}

export type LandingPageContent = {
  slug: string
  path: string
  title: string
  description: string
  eyebrow: string
  heroTitle: string
  intro: string
  toolTitle: string
  toolBody: string
  toolHref: string
  toolLabel: string
  highlights: string[]
  examples: SeoExampleItem[]
  faqs: SeoFaqItem[]
  related: SeoLinkItem[]
}

export type GuideContent = {
  slug: string
  path: string
  title: string
  description: string
  eyebrow: string
  heroTitle: string
  intro: string
  keyTakeaways: string[]
  sections: {
    title: string
    paragraphs: string[]
  }[]
  faqs: SeoFaqItem[]
  related: SeoLinkItem[]
}

export const landingPages: LandingPageContent[] = [
  {
    slug: "free-kundli",
    path: "/free-kundli",
    title: "Free Kundli Online",
    description:
      "Generate a free kundli online with AI-guided Vedic astrology reading, Lagna-based chart context, and follow-up answers rooted in your actual birth details.",
    eyebrow: "Free Kundli",
    heroTitle: "Generate a free kundli online and start asking real Vedic astrology questions.",
    intro:
      "This page is built for people looking for a free kundli online that goes beyond a static chart. Nakshatra AI helps you generate your chart, preserve the context, and ask chart-aware questions about life themes such as marriage, timing, career, family, and recurring patterns.",
    toolTitle: "Use the free kundli generator",
    toolBody:
      "Enter your birth details on the main reading form to create a kundli, save it to your account, and continue asking follow-up questions from the same Vedic chart context.",
    toolHref: "/#start-reading",
    toolLabel: "Open Free Kundli Tool",
    highlights: [
      "Free kundli generation tied to your signed-in account so saved readings stay available later.",
      "Chart-aware AI answers that remain anchored to Lagna, house lords, yogas, divisional charts, and dasha timing.",
      "Private session history so you can reopen earlier readings instead of starting from zero every time.",
    ],
    examples: [
      {
        title: "Career reading example",
        body:
          "A user generates a kundli, then asks when professional momentum is likely to strengthen, which houses and dashas support work changes, and what the D10 says about the current phase.",
      },
      {
        title: "Relationship reading example",
        body:
          "A user asks how the 7th house, Venus, Navamsa, and current dasha combine in the chart instead of getting a generic love-horoscope answer.",
      },
    ],
    faqs: [
      {
        question: "What is a free kundli online tool supposed to show?",
        answer:
          "A useful kundli tool should calculate the chart from your date, time, and place of birth, then help you understand the Lagna, planets, nakshatras, dasha sequence, and relevant divisional charts for the questions you care about.",
      },
      {
        question: "How is Nakshatra AI different from a static report?",
        answer:
          "Instead of only showing a chart image or one fixed report, Nakshatra AI keeps the chart context attached to the session so you can keep asking chart-based questions in natural language.",
      },
      {
        question: "Do I need exact birth time for a free kundli?",
        answer:
          "The closer the birth time is to the true time, the more reliable the Lagna, house placements, divisional charts, and dasha interpretation become. Even a few minutes can matter for some questions.",
      },
    ],
    related: [
      {
        href: "/ai-vedic-astrologer",
        label: "AI Vedic Astrologer",
        description: "See how the chart-aware chat layer works after the kundli is generated.",
      },
      {
        href: "/navamsa-chart",
        label: "Navamsa Chart Guide",
        description: "Understand why D9 matters for marriage, maturity, and deeper chart reading.",
      },
      {
        href: "/vimshottari-dasha",
        label: "Vimshottari Dasha",
        description: "Learn how timing periods shape the questions people ask after generating a kundli.",
      },
    ],
  },
  {
    slug: "ai-vedic-astrologer",
    path: "/ai-vedic-astrologer",
    title: "AI Vedic Astrologer",
    description:
      "Ask an AI Vedic astrologer questions based on your generated kundli, with chart-aware answers focused on houses, dashas, yogas, Navamsa, and Vedic timing logic.",
    eyebrow: "AI Vedic Astrologer",
    heroTitle: "Use an AI Vedic astrologer that answers from your chart, not from generic horoscope templates.",
    intro:
      "Many AI astrology products sound impressive but drift into generic output. Nakshatra AI is built around kundli context first and chat second, so questions about marriage, work, timing, finances, or emotional patterns remain grounded in the birth chart underneath.",
    toolTitle: "Start a chart-aware reading",
    toolBody:
      "Generate your kundli first, then ask focused questions about your chart. The AI reading flow is designed to keep your stored chart context attached to the session for follow-up analysis.",
    toolHref: "/#start-reading",
    toolLabel: "Start AI Vedic Reading",
    highlights: [
      "Answers are rooted in the generated chart rather than in sun-sign or template astrology.",
      "Recent readings stay attached to your account so you can continue the same line of questioning later.",
      "Built around Vedic chart logic including Lagna, house lords, dasha timing, and divisional chart context where available.",
    ],
    examples: [
      {
        title: "Timing example",
        body:
          "Ask when the chart is more supportive for job change, relocation, or marriage, and the answer can incorporate the relevant house lords and current dasha periods.",
      },
      {
        title: "Pattern example",
        body:
          "Ask why one emotional, family, or relationship pattern repeats in life and explore the recurring signatures in the natal chart rather than receiving a motivational placeholder.",
      },
    ],
    faqs: [
      {
        question: "Is the AI Vedic astrologer reading from my actual chart?",
        answer:
          "That is the goal of the product. The chat experience is attached to the generated kundli so follow-up questions remain tied to the same chart context instead of resetting into a generic chat.",
      },
      {
        question: "Can I ask about someone else’s chart?",
        answer:
          "Yes. If you have the birth details, you can generate another person’s kundli and ask chart-based questions from that reading too.",
      },
      {
        question: "Does an AI astrologer replace a human astrologer?",
        answer:
          "No. It can make chart exploration faster and more accessible, but it should still be treated as guidance rather than a replacement for professional legal, financial, medical, or life-critical judgment.",
      },
    ],
    related: [
      {
        href: "/free-kundli",
        label: "Free Kundli Online",
        description: "Generate the chart first so the AI reading has real chart context to work with.",
      },
      {
        href: "/kundli-matching",
        label: "Kundli Matching",
        description: "Explore chart comparison and relationship-oriented Vedic questions.",
      },
      {
        href: "/guides/marriage-indicators-in-a-vedic-chart",
        label: "Marriage Indicators",
        description: "See the kind of marriage analysis the AI should be grounding itself in.",
      },
    ],
  },
  {
    slug: "kundli-matching",
    path: "/kundli-matching",
    title: "Kundli Matching",
    description:
      "Explore kundli matching through chart-based compatibility questions, guna milan context, and Vedic relationship analysis anchored in both charts.",
    eyebrow: "Kundli Matching",
    heroTitle: "Kundli matching should compare real chart patterns, not only one score.",
    intro:
      "Compatibility in Vedic astrology is deeper than a single number. A serious kundli matching flow should look at lunar compatibility, relationship houses, Venus, Mars, Navamsa, and timing patterns alongside classical guna milan logic.",
    toolTitle: "Open the compatibility flow",
    toolBody:
      "Nakshatra AI includes compatibility analysis from the saved session, so once your own kundli is available you can open the matching flow and compare it against another set of birth details.",
    toolHref: "/#start-reading",
    toolLabel: "Generate Chart Before Matching",
    highlights: [
      "Matching should consider guna milan, but also the broader relationship signatures in both charts.",
      "Navamsa and timing matter because compatibility is not only about basic temperament fit.",
      "A good compatibility reading should explain where ease, friction, growth, and timing pressures are likely to appear.",
    ],
    examples: [
      {
        title: "Temperament fit example",
        body:
          "Two charts may score reasonably in guna milan but still show tension around emotional style, communication, or timing, which is why broader chart context matters.",
      },
      {
        title: "Marriage timing example",
        body:
          "A compatibility question often becomes more useful when it also looks at whether the current dashas of the two people are supportive or disruptive for commitment.",
      },
    ],
    faqs: [
      {
        question: "Is kundli matching only about guna milan?",
        answer:
          "No. Guna milan is one part of the picture. A fuller matching process also looks at relationship houses, Venus, Mars, Moon, Navamsa, and the broader promise and timing patterns in both charts.",
      },
      {
        question: "Can a lower guna score still lead to a workable relationship?",
        answer:
          "Sometimes yes. A lower score does not automatically define the whole relationship. The surrounding chart context can soften, complicate, or reshape what the raw score suggests.",
      },
      {
        question: "Why compare Navamsa as well?",
        answer:
          "Navamsa helps refine marriage and partnership themes, so it often gives important context for long-term relationship quality and maturity.",
      },
    ],
    related: [
      {
        href: "/navamsa-chart",
        label: "Navamsa Chart",
        description: "Understand why D9 matters so much in compatibility and marriage analysis.",
      },
      {
        href: "/guides/marriage-indicators-in-a-vedic-chart",
        label: "Marriage Indicators Guide",
        description: "Learn the broader chart factors behind relationship promise and timing.",
      },
      {
        href: "/free-kundli",
        label: "Free Kundli",
        description: "Generate the first chart before opening compatibility analysis.",
      },
    ],
  },
  {
    slug: "navamsa-chart",
    path: "/navamsa-chart",
    title: "Navamsa Chart",
    description:
      "Learn what the Navamsa chart means in Vedic astrology, why D9 matters for marriage and maturity, and how to connect it with the main kundli reading.",
    eyebrow: "Navamsa Chart",
    heroTitle: "The Navamsa chart helps refine what the main kundli is promising underneath.",
    intro:
      "In Vedic astrology, the Navamsa or D9 chart is one of the most important divisional charts. It is frequently used to understand marriage, dharma, maturity, inner strength, and the deeper condition of planets beyond the surface layer of the Rasi chart.",
    toolTitle: "Generate a kundli and view D9 where available",
    toolBody:
      "The easiest way to begin is to create a reading session from the home page, then open the chart viewer and inspect the available divisional chart features and chart-aware questions.",
    toolHref: "/#start-reading",
    toolLabel: "Open Kundli & D9 Flow",
    highlights: [
      "D9 is not a replacement for the natal chart. It refines and deepens it.",
      "Marriage questions often become much clearer when Rasi and Navamsa are read together.",
      "Planetary dignity and vargottama logic can change how strong or weak a placement really feels in lived experience.",
    ],
    examples: [
      {
        title: "Marriage refinement example",
        body:
          "A Venus placement that looks straightforward in D1 may behave very differently once D9 condition, sign support, and relationship timing are added to the interpretation.",
      },
      {
        title: "Maturity example",
        body:
          "Some planetary themes become more visible with age, and D9 often helps explain why a chart feels different in adulthood than it did earlier in life.",
      },
    ],
    faqs: [
      {
        question: "What is the Navamsa chart used for?",
        answer:
          "The Navamsa chart is commonly used to refine marriage analysis, dharma, inner strength, and the deeper expression of planets. It is one of the most important divisional charts in Jyotish.",
      },
      {
        question: "Should D9 be read without D1?",
        answer:
          "Usually no. The Rasi chart remains foundational. Navamsa is strongest when it is used to refine or confirm the natal chart rather than replace it.",
      },
      {
        question: "Why do people care so much about D9 in relationships?",
        answer:
          "Because long-term partnership themes, maturity, and the sustained quality of relational patterns often become clearer when the natal chart and Navamsa are judged together.",
      },
    ],
    related: [
      {
        href: "/kundli-matching",
        label: "Kundli Matching",
        description: "Navamsa becomes even more important when relationship comparison is involved.",
      },
      {
        href: "/guides/how-to-read-navamsa",
        label: "How to Read Navamsa",
        description: "Go deeper into D9 logic and what to look for first.",
      },
      {
        href: "/vimshottari-dasha",
        label: "Vimshottari Dasha",
        description: "Pair chart structure with timing periods for better Vedic interpretation.",
      },
    ],
  },
  {
    slug: "vimshottari-dasha",
    path: "/vimshottari-dasha",
    title: "Vimshottari Dasha",
    description:
      "Understand Vimshottari dasha in Vedic astrology, why it matters for timing, and how to connect mahadasha and antardasha periods with your kundli reading.",
    eyebrow: "Vimshottari Dasha",
    heroTitle: "Vimshottari dasha gives timing to the promise already shown in the chart.",
    intro:
      "A kundli can show themes and tendencies, but dashas help answer when those themes are likely to become active. Vimshottari dasha is one of the most widely used timing systems in Vedic astrology because it personalizes life periods based on the Moon’s nakshatra at birth.",
    toolTitle: "Ask timing questions from your chart",
    toolBody:
      "Create a chart session, then use the reading flow to ask when a marriage, career shift, financial opportunity, or emotionally difficult period is likely to become more active.",
    toolHref: "/#start-reading",
    toolLabel: "Ask a Dasha-Based Question",
    highlights: [
      "Dasha periods activate chart promise. They do not create an entirely different chart.",
      "Mahadasha gives the broader period; antardasha helps refine which theme is active within it.",
      "Timing questions become stronger when dasha analysis is paired with houses, lords, and divisional charts.",
    ],
    examples: [
      {
        title: "Career timing example",
        body:
          "A career question often becomes clearer when the active dasha is checked against the 10th house, its lord, work-oriented yogas, and D10 context.",
      },
      {
        title: "Relationship timing example",
        body:
          "Marriage or relationship timing often depends on whether the current periods are activating the 7th house, its lord, Venus, or relevant Navamsa themes.",
      },
    ],
    faqs: [
      {
        question: "What does Vimshottari dasha mean?",
        answer:
          "It is a planetary timing framework in Vedic astrology that divides life into major and sub-periods ruled by the nine grahas. It is derived from the Moon’s nakshatra at birth.",
      },
      {
        question: "Can dasha alone predict events?",
        answer:
          "Not safely. Dasha is strongest when it is judged together with the natal promise, current transits, relevant houses, and divisional chart support.",
      },
      {
        question: "Why is dasha important in AI-assisted astrology?",
        answer:
          "Because without timing logic, an answer can stay too broad. Dasha gives sequence and activation, which helps chart-based questions become more actionable.",
      },
    ],
    related: [
      {
        href: "/guides/what-vimshottari-dasha-means",
        label: "What Vimshottari Dasha Means",
        description: "Read a more detailed explainer of the timing logic and its practical use.",
      },
      {
        href: "/free-kundli",
        label: "Free Kundli",
        description: "Generate your chart first so dasha interpretation has the right foundation.",
      },
      {
        href: "/navamsa-chart",
        label: "Navamsa Chart",
        description: "Pair timing with deeper chart refinement for life-area interpretation.",
      },
    ],
  },
  {
    slug: "mangal-dosh",
    path: "/mangal-dosh",
    title: "Mangal Dosh",
    description:
      "Learn what Mangal Dosh means in Vedic astrology, where Mars placement matters, and why dosha analysis should be judged carefully within the full chart.",
    eyebrow: "Mangal Dosh",
    heroTitle: "Mangal Dosh should be judged carefully within the whole chart, not as a fear trigger.",
    intro:
      "Mars can strongly affect temperament, conflict style, sexuality, and partnership dynamics, which is why Mangal Dosh gets so much attention. But serious Vedic astrology should not reduce the entire marriage conversation to one dosha label.",
    toolTitle: "Generate your chart and ask about Mars properly",
    toolBody:
      "Use the kundli reading flow to inspect Mars in context, then ask chart-based questions about partnership, emotional intensity, conflict patterns, and whether the broader chart modifies the dosha discussion.",
    toolHref: "/#start-reading",
    toolLabel: "Check Mars in Your Chart",
    highlights: [
      "Mangal Dosh is often overused in fear-based astrology marketing.",
      "Mars must be judged together with houses, aspects, Venus, Moon, the 7th house, and broader compatibility context.",
      "A mature reading looks for both risk patterns and mitigating factors instead of only alarming labels.",
    ],
    examples: [
      {
        title: "Relationship tension example",
        body:
          "Mars can indicate drive, impatience, sexual intensity, or friction. Whether that becomes destructive, constructive, or manageable depends on the larger chart.",
      },
      {
        title: "Compatibility example",
        body:
          "In matching, Mars should be considered alongside the other person’s chart instead of being used as a standalone yes-or-no decision device.",
      },
    ],
    faqs: [
      {
        question: "Is Mangal Dosh always bad?",
        answer:
          "No. Mars can bring courage, initiative, drive, and intensity. The issue is how that energy behaves in the broader chart and in relationship contexts, not whether Mars is automatically bad.",
      },
      {
        question: "Why is Mangal Dosh often misunderstood?",
        answer:
          "Because it is commonly reduced to a fear-based checklist. A full Vedic reading should weigh house placement, aspects, planetary strength, cancellation factors, and relationship context.",
      },
      {
        question: "Can Mangal Dosh be judged without compatibility context?",
        answer:
          "Only partially. For marriage questions, comparison with the other chart is often important because one person’s Mars pattern may interact with the other chart in meaningful ways.",
      },
    ],
    related: [
      {
        href: "/kundli-matching",
        label: "Kundli Matching",
        description: "See how Mars behaves in relationship comparison instead of isolation.",
      },
      {
        href: "/guides/rahu-in-each-house",
        label: "Rahu in Each House",
        description: "Compare another high-anxiety topic with a more grounded chart-reading approach.",
      },
      {
        href: "/free-kundli",
        label: "Free Kundli",
        description: "Generate your chart first before drawing conclusions about doshas.",
      },
    ],
  },
  {
    slug: "daily-horoscope",
    path: "/daily-horoscope",
    title: "Daily Horoscope",
    description:
      "Explore a Vedic daily horoscope approach that respects chart context, transits, and timing instead of reducing the day to a generic sign message.",
    eyebrow: "Daily Horoscope",
    heroTitle: "A useful daily horoscope should respect your chart, not only your sign.",
    intro:
      "Daily horoscope content becomes more meaningful when it is tied to real timing logic rather than generic sign copy. In a Vedic context, today’s transits, the active dasha, Moon movement, and key house activations matter more than vague daily slogans.",
    toolTitle: "Begin with your chart before reading the day",
    toolBody:
      "Generate your kundli first so daily guidance can be interpreted through your own chart context rather than as a one-size-fits-all forecast.",
    toolHref: "/#start-reading",
    toolLabel: "Generate Your Chart First",
    highlights: [
      "Daily guidance is more useful when it connects to the natal chart and active timing periods.",
      "The Moon, transits, and current dasha can shift how one day feels from person to person.",
      "A chart-aware product can eventually make daily insights far more personal than sign-only horoscope content.",
    ],
    examples: [
      {
        title: "Decision day example",
        body:
          "One person may experience a transit as productive because it activates a supportive house, while another experiences it as draining because the same transit touches a vulnerable chart area.",
      },
      {
        title: "Mood example",
        body:
          "Daily emotional tone may track Moon movement, current antardasha, and natal sensitivities more closely than a broad zodiac column ever could.",
      },
    ],
    faqs: [
      {
        question: "How is a Vedic daily horoscope different from a generic horoscope?",
        answer:
          "A Vedic daily approach can consider chart-specific factors like the Moon, transits, house activations, and the current dasha instead of reducing the day to a broad sign summary.",
      },
      {
        question: "Should I trust a daily horoscope without my chart?",
        answer:
          "It can be entertaining or loosely directional, but chart-based timing is usually more useful when the goal is meaningful decision support rather than casual content.",
      },
      {
        question: "What makes daily guidance actually actionable?",
        answer:
          "Actionable guidance ties the day’s tone to the chart, clarifies where caution or momentum is likely, and explains why rather than only making vague predictions.",
      },
    ],
    related: [
      {
        href: "/panchang",
        label: "Panchang",
        description: "Pair daily guidance with tithi, nakshatra, yoga, and timing context.",
      },
      {
        href: "/vimshottari-dasha",
        label: "Vimshottari Dasha",
        description: "See how longer timing periods shape the importance of daily transits.",
      },
      {
        href: "/free-kundli",
        label: "Free Kundli",
        description: "Create the chart that daily guidance should ultimately be based on.",
      },
    ],
  },
  {
    slug: "panchang",
    path: "/panchang",
    title: "Panchang",
    description:
      "Learn what panchang means in Vedic timekeeping, why it matters for daily rhythm, and how tithi, nakshatra, yoga, and karana support better timing decisions.",
    eyebrow: "Panchang",
    heroTitle: "Panchang gives the day structure that many spiritual and practical decisions rest on.",
    intro:
      "Panchang is one of the most foundational daily tools in the Vedic tradition. It helps contextualize the day through tithi, nakshatra, yoga, karana, and weekday, which can shape spiritual practice, planning, and timing awareness.",
    toolTitle: "Pair daily timing with your chart",
    toolBody:
      "Panchang becomes more useful when it is read alongside your own chart and questions, so begin by generating a kundli and then explore how timing layers relate to your reading.",
    toolHref: "/#start-reading",
    toolLabel: "Start With Your Kundli",
    highlights: [
      "Panchang helps frame the quality of the day, not just the natal chart.",
      "It is especially useful for rituals, planning, and timing sensitivity.",
      "Nakshatra, tithi, and weekday logic can add daily nuance to longer chart-based cycles.",
    ],
    examples: [
      {
        title: "Planning example",
        body:
          "A person deciding when to begin a new effort may look at the day’s panchang quality together with the broader chart and timing picture rather than in isolation.",
      },
      {
        title: "Spiritual practice example",
        body:
          "Some days feel better suited for discipline, prayer, or reflective work because the panchang rhythm supports those qualities more clearly.",
      },
    ],
    faqs: [
      {
        question: "What does panchang include?",
        answer:
          "Panchang traditionally includes tithi, nakshatra, yoga, karana, and weekday, each of which adds a layer of meaning to the day’s timing and quality.",
      },
      {
        question: "Does panchang replace the birth chart?",
        answer:
          "No. Panchang describes the day. The natal chart describes the person. The two become more powerful when read together.",
      },
      {
        question: "Why do Vedic users care about panchang so much?",
        answer:
          "Because it helps connect action and ritual to time quality, which is central to many Vedic spiritual and astrological practices.",
      },
    ],
    related: [
      {
        href: "/daily-horoscope",
        label: "Daily Horoscope",
        description: "See how panchang can support more useful daily guidance.",
      },
      {
        href: "/guides/all-27-nakshatras-explained",
        label: "All 27 Nakshatras Explained",
        description: "Go deeper into one of the most important panchang components.",
      },
      {
        href: "/free-kundli",
        label: "Free Kundli",
        description: "Anchor daily timing awareness in your own chart structure too.",
      },
    ],
  },
]

export const guidePages: GuideContent[] = [
  {
    slug: "sun-in-12-houses-vedic-astrology",
    path: "/guides/sun-in-12-houses-vedic-astrology",
    title: "Sun in 12 Houses in Vedic Astrology",
    description:
      "Understand Sun in all 12 houses in Vedic astrology and how house placement changes authority, visibility, vitality, father themes, and life direction.",
    eyebrow: "Planet Guide",
    heroTitle: "Sun in the 12 houses changes how identity, authority, and vitality show up in life.",
    intro:
      "In Jyotish, the Sun represents identity, vitality, authority, confidence, father themes, dignity, and visible purpose. Its house placement changes where that fire gets expressed most strongly and where ego lessons become unavoidable.",
    keyTakeaways: [
      "The Sun’s house placement shows where dignity, will, and visibility seek expression.",
      "A strong Sun can support leadership, but it can also harden pride if not balanced well.",
      "House placement matters, but sign dignity, aspects, combustion patterns, and dasha timing still modify the result.",
    ],
    sections: [
      {
        title: "How to read the Sun first",
        paragraphs: [
          "Before judging house placement in isolation, look at the sign, house lord, aspects, dignity, and the larger Lagna context. A 10th-house Sun behaves differently depending on whether it is strengthened, afflicted, or supported by the chart.",
          "In Vedic astrology, the Sun is not only about personality in a modern psychological sense. It also relates to authority, confidence, father or paternal lineage themes, vitality, and the way a person carries visible responsibility.",
        ],
      },
      {
        title: "House-by-house overview",
        paragraphs: [
          "Sun in the 1st emphasizes identity, visibility, and self-directed will. In the 2nd it can affect speech, family dignity, and values. In the 3rd it strengthens initiative and courage. In the 4th it can shift attention toward status, inner stability, mother, or home foundations.",
          "In the 5th it highlights intelligence, creativity, and children-related themes. In the 6th it can fight enemies or increase strain through conflict. In the 7th it intensifies partnership dynamics and public dealings. In the 8th it can bring transformation, vulnerability, and inheritance themes into focus.",
          "In the 9th it can strongly connect to dharma, father, teachers, or higher purpose. In the 10th it often boosts public role, ambition, and karma in visible ways. In the 11th it can increase desire for gains, networks, and recognition. In the 12th it can redirect vitality toward retreat, foreign links, loss, sacrifice, or inner work.",
        ],
      },
      {
        title: "Why this still needs full-chart context",
        paragraphs: [
          "Sun in a house does not speak alone. The house lord, aspects from Jupiter, Saturn, Mars, Rahu, or Ketu, and the operative dasha can dramatically change whether the placement feels noble, pressured, egoic, fatigued, or constructive.",
        ],
      },
    ],
    faqs: [
      {
        question: "Is Sun in the 10th always the best placement?",
        answer:
          "Not automatically. It can support visibility and status, but the condition of the chart still decides whether that visibility becomes healthy leadership, pressure, or ego conflict.",
      },
      {
        question: "Does Sun in the 12th mean weak identity?",
        answer:
          "Not necessarily. It can point toward private work, retreat, foreign ties, or sacrifice themes, but the sign, dignity, and whole chart determine how constructive or draining that expression becomes.",
      },
    ],
    related: [
      {
        href: "/free-kundli",
        label: "Generate Your Kundli",
        description: "Check where the Sun actually sits in your chart before interpreting it.",
      },
      {
        href: "/ai-vedic-astrologer",
        label: "Ask the AI Vedic Astrologer",
        description: "Use your chart context to ask what your Sun placement means in practice.",
      },
    ],
  },
  {
    slug: "all-27-nakshatras-explained",
    path: "/guides/all-27-nakshatras-explained",
    title: "All 27 Nakshatras Explained",
    description:
      "A practical guide to all 27 nakshatras in Vedic astrology, including what nakshatras mean, why the Moon matters, and how they shape personality and timing.",
    eyebrow: "Nakshatra Guide",
    heroTitle: "All 27 nakshatras add nuance that the zodiac signs alone cannot provide.",
    intro:
      "Nakshatras are the lunar mansions of Vedic astrology. They help refine temperament, instinct, emotional patterning, naming sounds, timing, and dasha logic in ways that the twelve signs alone cannot.",
    keyTakeaways: [
      "Nakshatras add finer-grained texture to chart interpretation.",
      "Moon nakshatra is especially important because it influences Vimshottari dasha and emotional life.",
      "The nakshatra, its pada, ruling deity, and planetary ruler can all refine meaning.",
    ],
    sections: [
      {
        title: "Why nakshatras matter",
        paragraphs: [
          "A person’s Moon sign may be the same as someone else’s, but their Moon nakshatra can make their inner style feel very different. Nakshatras bring sensitivity, symbolism, instinct, and timing detail to the reading.",
        ],
      },
      {
        title: "The 27 nakshatras at a glance",
        paragraphs: [
          "Ashwini begins with speed and initiation, Bharani intensifies carrying and pressure, Krittika cuts and purifies, Rohini grows and nourishes, and Mrigashira searches and explores.",
          "Ardra breaks and renews, Punarvasu restores, Pushya nourishes and stabilizes, Ashlesha coils and binds, Magha honors lineage, and Purva Phalguni seeks pleasure and expression.",
          "Uttara Phalguni stabilizes and formalizes, Hasta shapes and handles, Chitra beautifies and constructs, Swati disperses and adapts, Vishakha strives and focuses, and Anuradha bonds with devotion.",
          "Jyeshtha protects status, Mula uproots, Purva Ashadha pushes conviction, Uttara Ashadha stabilizes victory, Shravana listens and learns, Dhanishta rhythms and amplifies, and Shatabhisha isolates and heals.",
          "Purva Bhadrapada intensifies inner fire, Uttara Bhadrapada deepens steadiness, and Revati guides, protects, and completes.",
        ],
      },
      {
        title: "How to use nakshatras in practice",
        paragraphs: [
          "Nakshatra work is strongest when tied to the Moon, relevant planets, dasha periods, and the life area being judged. It is not just personality flavoring; it directly affects timing and interpretive depth.",
        ],
      },
    ],
    faqs: [
      {
        question: "Is Moon nakshatra more important than Sun sign in Vedic astrology?",
        answer:
          "For many Vedic purposes, yes. The Moon and its nakshatra are highly important because they shape timing, mind, and experiential life in a very direct way.",
      },
      {
        question: "Do I need the pada too?",
        answer:
          "Yes, when you want finer detail. The pada can refine temperament, varga logic, and sometimes naming and spiritual orientation.",
      },
    ],
    related: [
      {
        href: "/panchang",
        label: "Panchang Guide",
        description: "See how daily nakshatra timing connects with broader Vedic day quality.",
      },
      {
        href: "/vimshottari-dasha",
        label: "Vimshottari Dasha",
        description: "Moon nakshatra is one of the foundations of the dasha sequence.",
      },
    ],
  },
  {
    slug: "how-to-read-navamsa",
    path: "/guides/how-to-read-navamsa",
    title: "How to Read Navamsa",
    description:
      "Learn how to read Navamsa in Vedic astrology, what to look at first, and how to connect D9 with the natal chart for marriage and maturity questions.",
    eyebrow: "Chart Guide",
    heroTitle: "Reading Navamsa starts by connecting D9 back to the natal promise.",
    intro:
      "Navamsa is one of the most important divisional charts in Vedic astrology, but it is often misunderstood. The safest way to read it is to start with the natal promise, then use D9 to refine strength, maturity, marriage themes, and the deeper expression of planets.",
    keyTakeaways: [
      "Always start with D1 before moving to D9.",
      "Look at the D9 Lagna, key house lords, Venus, Jupiter, and the condition of planets that matter most to the topic.",
      "Navamsa often becomes clearer with age and experience.",
    ],
    sections: [
      {
        title: "A practical reading order",
        paragraphs: [
          "Begin with the natal chart and identify the houses and planets tied to the question. Then check the same significators in D9 to see whether the deeper expression looks stronger, weaker, or more complex than the D1 alone suggested.",
        ],
      },
      {
        title: "What Navamsa refines",
        paragraphs: [
          "Navamsa is often central to marriage, dharma, inner maturity, and planetary refinement. It can show whether a placement gains depth, dignity, steadiness, or strain beneath the surface layer.",
        ],
      },
      {
        title: "Common mistakes",
        paragraphs: [
          "The biggest mistake is reading D9 as if it replaces the natal chart. Another is overreacting to one placement without checking the Lagna, lords, aspects, and the relevant topic-specific indicators.",
        ],
      },
    ],
    faqs: [
      {
        question: "What should I check first in Navamsa?",
        answer:
          "Usually the D9 Lagna, the condition of the key planets relevant to the question, and whether the natal chart promise is being reinforced or modified.",
      },
      {
        question: "Is Navamsa only for marriage?",
        answer:
          "No. Marriage is one major use, but D9 also helps with planetary maturity, dharma, and deeper life-expression questions.",
      },
    ],
    related: [
      {
        href: "/navamsa-chart",
        label: "Navamsa Chart",
        description: "Return to the main D9 landing page for a shorter overview.",
      },
      {
        href: "/kundli-matching",
        label: "Kundli Matching",
        description: "See why Navamsa becomes so important in relationship analysis.",
      },
    ],
  },
  {
    slug: "what-vimshottari-dasha-means",
    path: "/guides/what-vimshottari-dasha-means",
    title: "What Vimshottari Dasha Means",
    description:
      "A practical explanation of what Vimshottari dasha means in Vedic astrology and how to think about mahadasha, antardasha, and chart activation.",
    eyebrow: "Timing Guide",
    heroTitle: "Vimshottari dasha means the chart is being activated in sequence over time.",
    intro:
      "People often hear about Vimshottari dasha as if it were a mystical countdown. In practice, it is a structured timing model in Vedic astrology that helps show which planetary themes are being activated during different phases of life.",
    keyTakeaways: [
      "Dashas help answer when, not only what.",
      "The operating planet activates the chart promise it is connected to.",
      "Mahadasha sets the broader climate and antardasha sharpens it.",
    ],
    sections: [
      {
        title: "What a dasha period is really doing",
        paragraphs: [
          "A dasha period does not erase the natal chart. Instead, it foregrounds the houses, lords, aspects, and signatures tied to the ruling planet. That is why the same career period can feel expansive in one chart and pressured in another.",
        ],
      },
      {
        title: "Mahadasha and antardasha",
        paragraphs: [
          "The mahadasha gives the broad environment or chapter. The antardasha shows the more immediate active subtheme inside that chapter. Strong interpretation comes from connecting both to the natal chart and the actual question being asked.",
        ],
      },
      {
        title: "Why timing should stay grounded",
        paragraphs: [
          "Timing becomes unreliable if it is separated from the natal promise, transits, and the relevant divisional context. Dasha is a pillar, not the entire building.",
        ],
      },
    ],
    faqs: [
      {
        question: "Can Vimshottari dasha predict exact dates?",
        answer:
          "Usually it is better at revealing active periods and windows than exact dates in isolation. More precise timing usually needs additional methods and careful synthesis.",
      },
      {
        question: "Why is the Moon so important here?",
        answer:
          "Because the Vimshottari sequence begins from the Moon’s nakshatra at birth, which makes lunar placement central to the system.",
      },
    ],
    related: [
      {
        href: "/vimshottari-dasha",
        label: "Vimshottari Dasha",
        description: "Return to the main timing landing page and use it with your chart.",
      },
      {
        href: "/guides/all-27-nakshatras-explained",
        label: "All 27 Nakshatras",
        description: "See the nakshatra layer that underpins the dasha sequence.",
      },
    ],
  },
  {
    slug: "rahu-in-each-house",
    path: "/guides/rahu-in-each-house",
    title: "Rahu in Each House",
    description:
      "Understand Rahu in each house in Vedic astrology and how amplification, desire, obsession, worldly appetite, and disruption behave across life areas.",
    eyebrow: "Node Guide",
    heroTitle: "Rahu in each house shows where appetite, amplification, and unusual hunger become strongest.",
    intro:
      "Rahu often gets described dramatically, but it is more useful to understand it as an amplifier, distorter, and worldly intensifier. Its house placement shows where desire, fascination, experimentation, and instability can become especially prominent.",
    keyTakeaways: [
      "Rahu amplifies the house it occupies.",
      "Its results vary sharply depending on sign, aspects, and the overall chart.",
      "Rahu can bring both innovation and confusion in the life area it touches.",
    ],
    sections: [
      {
        title: "How to judge Rahu sensibly",
        paragraphs: [
          "Rahu should not be reduced to fear language. It can indicate ambition, experimentation, foreignness, obsession, ambition, unconventionality, and intense worldly focus, but the outcome depends on the larger chart.",
        ],
      },
      {
        title: "House themes",
        paragraphs: [
          "In the 1st house Rahu can intensify identity and self-projection. In the 2nd it may amplify family, speech, or wealth hunger. In the 3rd it can sharpen risk-taking and skill ambition. In the 4th it may complicate inner peace, home, or belonging.",
          "In the 5th it can intensify romance, speculation, or children themes. In the 6th it can fight hard through competition and conflict. In the 7th it can destabilize or intensify partnership appetite. In the 8th it can magnify secrecy, taboo, and transformation.",
          "In the 9th it can complicate belief or teacher dynamics. In the 10th it often pushes public ambition. In the 11th it can drive gains and networks strongly. In the 12th it can create unusual loss, foreign, retreat, or subconscious patterns.",
        ],
      },
      {
        title: "Rahu always needs Ketu context too",
        paragraphs: [
          "Because Rahu and Ketu operate as an axis, Rahu’s appetite should be judged together with the detachment and inherited pattern on the opposite side of the chart.",
        ],
      },
    ],
    faqs: [
      {
        question: "Is Rahu always negative?",
        answer:
          "No. Rahu can bring innovation, bold worldly growth, unusual openings, and social reach. The challenge is that it often comes with excess, confusion, or instability if not handled well.",
      },
      {
        question: "Why does Rahu feel so intense?",
        answer:
          "Because it magnifies appetite and fixation in the house it occupies, which can create urgency, fascination, or imbalance around that life area.",
      },
    ],
    related: [
      {
        href: "/mangal-dosh",
        label: "Mangal Dosh",
        description: "Compare another often over-dramatized chart topic with a more grounded explanation.",
      },
      {
        href: "/free-kundli",
        label: "Generate Your Kundli",
        description: "Check your actual Rahu house placement in context.",
      },
    ],
  },
  {
    slug: "marriage-indicators-in-a-vedic-chart",
    path: "/guides/marriage-indicators-in-a-vedic-chart",
    title: "Marriage Indicators in a Vedic Chart",
    description:
      "Learn the main marriage indicators in a Vedic chart, including the 7th house, Venus, Navamsa, dasha timing, and compatibility context.",
    eyebrow: "Marriage Guide",
    heroTitle: "Marriage indicators in a Vedic chart come from pattern synthesis, not one single factor.",
    intro:
      "Questions about marriage are some of the most common in astrology, but good Vedic interpretation does not rely on one yoga, one dosha, or one transit. It looks at the 7th house, its lord, Venus, Moon, Navamsa, relevant yogas, and timing systems together.",
    keyTakeaways: [
      "The 7th house is crucial, but never enough by itself.",
      "Venus, Navamsa, and operative dashas often change the practical reading significantly.",
      "Compatibility and timing are separate but related questions.",
    ],
    sections: [
      {
        title: "What to judge first",
        paragraphs: [
          "Start with the 7th house, the 7th lord, Venus, and the condition of relationship-relevant houses and planets. Then refine with Navamsa and timing systems such as Vimshottari dasha.",
        ],
      },
      {
        title: "What often gets missed",
        paragraphs: [
          "People often focus only on dosha labels or one yoga, but marriage outcomes are shaped by emotional readiness, chart maturity, broader relational patterning, and whether the active period supports commitment.",
        ],
      },
      {
        title: "Promise versus timing",
        paragraphs: [
          "A chart can show relationship promise but not immediate timing. Another chart may have timing pressure but weak stability. Good marriage reading has to separate those layers before combining them again.",
        ],
      },
    ],
    faqs: [
      {
        question: "Can one chart factor decide marriage outcome?",
        answer:
          "Rarely. Marriage interpretation is usually a synthesis problem, which is why serious Vedic analysis looks at multiple indicators together.",
      },
      {
        question: "Why is Navamsa so important here?",
        answer:
          "Because Navamsa helps refine relationship quality, maturity, and deeper marital patterns beyond the surface layer of the natal chart.",
      },
    ],
    related: [
      {
        href: "/kundli-matching",
        label: "Kundli Matching",
        description: "Apply these marriage indicators to relationship comparison.",
      },
      {
        href: "/navamsa-chart",
        label: "Navamsa Chart",
        description: "Go deeper into the D9 logic that supports marriage interpretation.",
      },
    ],
  },
  {
    slug: "what-life-path-number-means",
    path: "/guides/what-life-path-number-means",
    title: "What Life Path Number Means in Numerology",
    description:
      "Learn what a Life Path number means in numerology, why it is calculated from the full birth date, and how it shapes the deeper arc of a reading.",
    eyebrow: "Numerology Guide",
    heroTitle: "The Life Path number is the backbone of a numerology reading.",
    intro:
      "In numerology, the Life Path number is usually treated as the central current of the reading. It is derived from the full birth date and is used to describe the broader road of growth, lessons, patterns, and direction that life keeps unfolding through.",
    keyTakeaways: [
      "Life Path is calculated from the full birth date rather than from the name.",
      "It usually describes the deeper path of growth rather than a passing mood or trait.",
      "A Life Path number is strongest when read together with the other core numbers, not in total isolation.",
    ],
    sections: [
      {
        title: "Why the Life Path number matters first",
        paragraphs: [
          "When people first explore numerology, the Life Path number is often the starting point because it gives the broadest sense of direction. It is meant to describe the kind of lessons, internal development, and recurring themes that shape the life journey over time.",
          "This is why readers often speak about the Life Path as the road beneath the road. It does not explain every detail of personality, but it gives a strong sense of what life is trying to teach and what kind of growth keeps becoming unavoidable.",
        ],
      },
      {
        title: "What it does and does not describe",
        paragraphs: [
          "A Life Path number is not meant to explain your entire identity. It is not the same thing as your emotional needs, your social impression, or the way your gifts become visible in the world. Instead, it acts more like the larger chapter structure of your life.",
          "That is why a person may have a Life Path that feels quiet, reflective, and inward, while still appearing expressive or sociable on the surface. Other numerology numbers refine what the Life Path begins.",
        ],
      },
      {
        title: "How to use Life Path in a real reading",
        paragraphs: [
          "A useful way to read the Life Path is to ask: what kinds of experiences keep maturing this person, even when the outer circumstances change? What life themes repeat until they are understood more deeply?",
          "In a full reading, Life Path is usually strongest when it is read alongside Destiny, Soul Urge, Personality, Birthday, and Attitude so the interpretation feels layered rather than one-note.",
        ],
      },
    ],
    faqs: [
      {
        question: "Is Life Path the most important number in numerology?",
        answer:
          "It is often treated as the most central number, but not the only important one. It works best as the backbone of the reading, with other numbers adding nuance and detail.",
      },
      {
        question: "Why is Life Path based on the birth date?",
        answer:
          "Because numerology uses the birth date to describe the larger life road and developmental arc, while name-based numbers are usually used to describe expression, desire, or outer style.",
      },
    ],
    related: [
      {
        href: "/guides/what-destiny-number-means",
        label: "What Destiny Number Means",
        description: "See how the life road differs from the way your gifts want to be expressed outwardly.",
      },
      {
        href: "/numerology",
        label: "Try the Numerology Reading",
        description: "Return to the main numerology page and see your own Life Path in context.",
      },
    ],
  },
  {
    slug: "what-destiny-number-means",
    path: "/guides/what-destiny-number-means",
    title: "What Destiny Number Means in Numerology",
    description:
      "Understand what a Destiny number means in numerology, how it is derived from the full name, and why it speaks to contribution, talent, and outer expression.",
    eyebrow: "Numerology Guide",
    heroTitle: "The Destiny number describes how your gifts want to become visible in the world.",
    intro:
      "If the Life Path shows the broader road of growth, the Destiny number shows the form your gifts naturally want to take in visible life. It is calculated from the full name and is often used to understand expression, contribution, talent, and outer impact.",
    keyTakeaways: [
      "Destiny is derived from the full letters in the name rather than the birth date.",
      "It is often read as a number of expression, contribution, talent, and visible purpose.",
      "Destiny refines the Life Path by showing how the inner road tends to take form outwardly.",
    ],
    sections: [
      {
        title: "What Destiny is trying to show",
        paragraphs: [
          "The Destiny number often answers the question: if this person’s deeper path is maturing inwardly, what shape does that path want to take in the outer world? It can speak to expression, contribution, work style, creative direction, and the kind of imprint a person naturally leaves behind.",
          "That does not mean it predicts one exact profession or one single life role. Instead, it gives a style of contribution that may appear through many forms over time.",
        ],
      },
      {
        title: "How it differs from Life Path and Soul Urge",
        paragraphs: [
          "Life Path is broader and more developmental. Soul Urge is more private and emotional. Destiny sits between the two by showing how a person’s deeper qualities want to be translated into visible life.",
          "This is why someone may feel one thing internally, grow through another theme over the course of life, and still express their gifts outwardly in a distinct third style. Destiny helps explain that outer expression.",
        ],
      },
      {
        title: "How to read it more wisely",
        paragraphs: [
          "The most helpful way to read Destiny is not to reduce it to career clichés. Instead, ask what kind of contribution this number is pointing toward. Is the person here to teach, build, create, care, organize, guide, heal, or initiate in a certain style?",
          "A mature reading uses Destiny as an expression pattern, not a rigid label. It becomes most meaningful when read alongside the rest of the chart of numbers.",
        ],
      },
    ],
    faqs: [
      {
        question: "Is Destiny number the same as career number?",
        answer:
          "Not exactly. It can influence the way career and contribution unfold, but it is broader than job title alone. It is more about the style of expression and visible impact.",
      },
      {
        question: "Why is Destiny taken from the full name?",
        answer:
          "Because numerology treats the full name as part of the outward pattern of expression and identity, making it a natural source for a number tied to contribution and visibility.",
      },
    ],
    related: [
      {
        href: "/guides/what-life-path-number-means",
        label: "What Life Path Number Means",
        description: "Compare the outer expression number with the deeper road of growth.",
      },
      {
        href: "/guides/what-personality-number-means",
        label: "What Personality Number Means",
        description: "See how Destiny differs from the first social impression people often feel.",
      },
    ],
  },
  {
    slug: "what-soul-urge-number-means",
    path: "/guides/what-soul-urge-number-means",
    title: "What Soul Urge Number Means in Numerology",
    description:
      "Learn what a Soul Urge number means in numerology, why it is taken from the vowels of the name, and how it relates to inner desire and emotional truth.",
    eyebrow: "Numerology Guide",
    heroTitle: "The Soul Urge number points to what your heart quietly wants underneath the surface.",
    intro:
      "Soul Urge is one of the most inward-facing numerology numbers. It is derived from the vowels in the name and is often used to describe what feels emotionally true, nourishing, and deeply desired beneath outward roles and social performance.",
    keyTakeaways: [
      "Soul Urge is usually calculated from the vowels in the full name.",
      "It is used to understand inner desire, emotional truth, and what feels deeply fulfilling.",
      "Soul Urge often explains the difference between outer appearance and inner need.",
    ],
    sections: [
      {
        title: "Why Soul Urge feels so personal",
        paragraphs: [
          "Unlike more outward numbers, Soul Urge speaks to the private emotional core. It often describes what the person longs for, what kind of inner nourishment matters most, and what the heart is quietly moving toward even when life is noisy on the surface.",
          "This is one reason Soul Urge can feel surprisingly accurate. It often names a motivation that is real even if it is not immediately visible to everyone else.",
        ],
      },
      {
        title: "How it differs from Personality",
        paragraphs: [
          "Personality is more about the first impression or outer tone. Soul Urge is what lies beneath that. A person may appear steady, polished, and highly responsible to others while internally longing for freedom, expression, intimacy, peace, or recognition in a very different way.",
          "This difference between inner and outer style is a major reason numerology becomes more interesting when the numbers are read together rather than separately.",
        ],
      },
      {
        title: "How to use Soul Urge in a reading",
        paragraphs: [
          "A useful question to ask is: what does this person’s heart keep moving toward, even when life becomes distracting or demanding? The Soul Urge number often answers that question more clearly than the outer numbers do.",
          "It is especially valuable in readings about fulfillment, emotional restlessness, recurring dissatisfaction, and the difference between success and true nourishment.",
        ],
      },
    ],
    faqs: [
      {
        question: "Is Soul Urge the same as personality?",
        answer:
          "No. Soul Urge is inward and emotional, while Personality is outward and social. The two can support each other or feel very different from one another.",
      },
      {
        question: "Why is Soul Urge taken from vowels?",
        answer:
          "In numerology, vowels are traditionally treated as revealing a quieter inner current, which is why they are used for the number associated with desire and emotional truth.",
      },
    ],
    related: [
      {
        href: "/guides/what-personality-number-means",
        label: "What Personality Number Means",
        description: "Compare the inner emotional number with the outer social tone.",
      },
      {
        href: "/guides/what-life-path-number-means",
        label: "What Life Path Number Means",
        description: "See how inner desire differs from the broader road of growth.",
      },
    ],
  },
  {
    slug: "what-personality-number-means",
    path: "/guides/what-personality-number-means",
    title: "What Personality Number Means in Numerology",
    description:
      "Understand what a Personality number means in numerology, how it is derived from the consonants in the name, and why it shapes first impressions and outer tone.",
    eyebrow: "Numerology Guide",
    heroTitle: "The Personality number describes the social doorway through which others often meet you.",
    intro:
      "The Personality number is usually derived from the consonants in the full name. In numerology, it is often used to describe first impressions, outer tone, visible style, and the way a person’s energy is initially received by others.",
    keyTakeaways: [
      "Personality is more about social impression than deeper emotional truth.",
      "It often explains what people notice first before they know the full person.",
      "It becomes most useful when compared with Soul Urge and Destiny.",
    ],
    sections: [
      {
        title: "What Personality is actually showing",
        paragraphs: [
          "The Personality number does not claim to reveal your entire nature. It is narrower than that. Its job is to show the tone, atmosphere, and social style that people often encounter first.",
          "This can include the way your energy comes across, the kind of emotional signal you give off, and the qualities others may assume about you before they understand the deeper layers underneath.",
        ],
      },
      {
        title: "Why it matters in a reading",
        paragraphs: [
          "Many people have a real difference between how they feel inside and how they are perceived from the outside. Personality is often the number that explains that gap most clearly.",
          "That makes it especially useful when a person feels misunderstood, overly simplified by others, or surprised by the kinds of assumptions people project onto them.",
        ],
      },
      {
        title: "How to read it with more depth",
        paragraphs: [
          "A good numerology reading does not treat Personality as a shallow label. Instead, it asks how the outer tone is interacting with the inner life and the larger path. Is the social mask aligned with the emotional truth, or does it partly protect it?",
          "This is why Personality becomes more meaningful when read together with Soul Urge and Destiny rather than by itself.",
        ],
      },
    ],
    faqs: [
      {
        question: "Does Personality number show who I really am?",
        answer:
          "Only partly. It is more about the outer doorway, not the entire interior world. It becomes most accurate when paired with the more inward-facing numbers.",
      },
      {
        question: "Why is Personality based on consonants?",
        answer:
          "Traditional numerology uses consonants to represent the more outward structure of the name, making them a natural source for the number tied to visible style and impression.",
      },
    ],
    related: [
      {
        href: "/guides/what-soul-urge-number-means",
        label: "What Soul Urge Number Means",
        description: "See how the outer social tone differs from the private emotional truth.",
      },
      {
        href: "/guides/what-destiny-number-means",
        label: "What Destiny Number Means",
        description: "Compare first impression with the broader style of outer expression and contribution.",
      },
    ],
  },
  {
    slug: "what-birthday-number-means",
    path: "/guides/what-birthday-number-means",
    title: "What Birthday Number Means in Numerology",
    description:
      "Learn what a Birthday number means in numerology, why it is taken from the day you were born, and how it adds a natural talent or flavor to the reading.",
    eyebrow: "Numerology Guide",
    heroTitle: "The Birthday number adds a natural gift or flavor to the larger reading.",
    intro:
      "The Birthday number is a supporting number taken from the calendar day on which you were born. It is not usually treated as the backbone of the reading, but it often adds a recognizable talent, instinct, or repeating style that colors the whole profile.",
    keyTakeaways: [
      "Birthday number is derived from the day of birth rather than the full date.",
      "It often points to a natural gift, instinctive strength, or familiar life flavor.",
      "It is a supporting influence, not usually the central axis of the whole reading.",
    ],
    sections: [
      {
        title: "Why Birthday number feels specific",
        paragraphs: [
          "Because it comes only from the day of birth, the Birthday number often feels narrower and more precise than the broader Life Path. It can show a natural strength, a familiar instinct, or a quality that seems to show up easily in the personality.",
          "This is one reason it often feels like a subtle but recognizable accent in the reading rather than the whole composition.",
        ],
      },
      {
        title: "What it adds to a numerology profile",
        paragraphs: [
          "A person’s Life Path may describe the larger road, but the Birthday number often explains something about how the person naturally moves within that road. It can add charm, discipline, intuition, sensitivity, boldness, or another recurring flavor depending on the number involved.",
          "In practice, this is often the number that helps explain why two people with similar larger patterns still feel different in their everyday style.",
        ],
      },
      {
        title: "How to read it without overusing it",
        paragraphs: [
          "The Birthday number is most helpful when treated as a supporting tone. It adds texture and nuance, but it usually should not be allowed to override the larger pattern shown by the core numbers.",
          "Think of it as a natural gift or familiar accent rather than the final authority on the whole reading.",
        ],
      },
    ],
    faqs: [
      {
        question: "Is Birthday number as important as Life Path?",
        answer:
          "Usually no. It is generally treated as a supporting influence that adds flavor, talent, or nuance rather than replacing the main reading axis.",
      },
      {
        question: "Why use the day of birth by itself?",
        answer:
          "Because numerology treats the birth day as a compact supporting signal that often reveals a natural quality or instinctive style present from early on.",
      },
    ],
    related: [
      {
        href: "/guides/what-attitude-number-means",
        label: "What Attitude Number Means",
        description: "Compare Birthday’s supporting tone with the energy you naturally lead with.",
      },
      {
        href: "/guides/what-life-path-number-means",
        label: "What Life Path Number Means",
        description: "See how the day-of-birth influence differs from the larger road of life.",
      },
    ],
  },
  {
    slug: "what-attitude-number-means",
    path: "/guides/what-attitude-number-means",
    title: "What Attitude Number Means in Numerology",
    description:
      "Understand what an Attitude number means in numerology, how it is derived from birth month and day, and why it relates to first approach and immediate tone.",
    eyebrow: "Numerology Guide",
    heroTitle: "The Attitude number describes the energy you often lead with at first contact.",
    intro:
      "The Attitude number is usually derived from the month and day of birth together. In numerology, it is often used to describe the tone you naturally bring into new situations, first impressions, and the way you initially meet life before deeper layers unfold.",
    keyTakeaways: [
      "Attitude is usually calculated from the birth month and day together.",
      "It often describes first response, social entry point, and initial tone.",
      "It is a supporting influence that helps explain how you begin things or meet the world at first contact.",
    ],
    sections: [
      {
        title: "Why Attitude feels immediate",
        paragraphs: [
          "Some numbers in numerology feel deep and long-range, while others feel immediate. Attitude belongs more to that second category. It often describes the first way you approach people, situations, and fresh chapters before your deeper nature fully reveals itself.",
          "This is why it can feel especially accurate around first impressions, reactions, and instinctive social posture.",
        ],
      },
      {
        title: "What it can explain",
        paragraphs: [
          "The Attitude number can help explain why a person seems bold at first, cautious at first, warm at first, analytical at first, or unusually energetic at first contact. It is often less about the whole personality and more about the opening tone of the encounter.",
          "That makes it especially useful when someone wants to understand how they tend to enter rooms, conversations, or new life chapters.",
        ],
      },
      {
        title: "How to keep it in proportion",
        paragraphs: [
          "Attitude should not be mistaken for the whole reading. It is a useful secondary lens, but it becomes much more meaningful when it is read next to the larger numerology structure rather than as a standalone verdict.",
          "In practice, it often works best as an explanation for first tone, while the deeper numbers explain the fuller character underneath.",
        ],
      },
    ],
    faqs: [
      {
        question: "Is Attitude the same as Personality number?",
        answer:
          "Not exactly. Both can affect first impression, but Attitude is more about initial approach and entry tone, while Personality is more about the consistent outer style people tend to perceive.",
      },
      {
        question: "Why is Attitude taken from month and day?",
        answer:
          "Because numerology treats that part of the birth date as a compact signal for immediate style, first response, and the tone with which a person tends to approach life.",
      },
    ],
    related: [
      {
        href: "/guides/what-personality-number-means",
        label: "What Personality Number Means",
        description: "See how Attitude differs from the broader outer impression people receive from you.",
      },
      {
        href: "/guides/what-birthday-number-means",
        label: "What Birthday Number Means",
        description: "Compare the energy you lead with to the supporting gift or flavor in your chart.",
      },
    ],
  },
]

export const allSeoPaths = [
  "/",
  "/numerology",
  "/about",
  "/contact",
  "/privacy",
  "/guides",
  ...landingPages.map((page) => page.path),
  ...guidePages.map((page) => page.path),
]

export function getLandingPageBySlug(slug: string) {
  return landingPages.find((page) => page.slug === slug)
}

export function getGuidePageBySlug(slug: string) {
  return guidePages.find((page) => page.slug === slug)
}

export function getLandingPageOrThrow(slug: string) {
  const page = getLandingPageBySlug(slug)
  if (!page) {
    throw new Error(`Missing landing page content for slug: ${slug}`)
  }
  return page
}
