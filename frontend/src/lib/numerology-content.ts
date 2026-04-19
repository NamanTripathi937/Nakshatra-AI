export type NumerologyKey =
  | "life_path"
  | "destiny"
  | "soul_urge"
  | "personality"
  | "birthday"
  | "attitude"

export type NumerologyNumber = {
  key: NumerologyKey
  label: string
  number: number
  raw_total: number
  title: string
  essence: string
  keywords: string[]
  gifts: string[]
  growth: string[]
  calculation: string
  reduction: string
}

type Archetype = {
  aura: string
  portrait: string
  aligned: string
  shadow: string
  relationships: string
  work: string
  growth: string
  spiritual: string
}

type CardCopy = {
  intro: string
  body: string
  alignedTitle: string
  alignedBody: string
  growthTitle: string
  growthBody: string
}

type InsightSection = {
  title: string
  body: string
}

const ARCHETYPES: Record<number, Archetype> = {
  1: {
    aura: "self-starting fire",
    portrait:
      "The energy of 1 wants to initiate, define, and move first. It often appears in the lives of people who are being asked to trust their own instincts rather than waiting for permission from the outside world.",
    aligned:
      "When this number is expressed well, it brings bravery, clean decision-making, and the willingness to begin again without drama. It gives a person the power to set direction for themselves and often for others too.",
    shadow:
      "When strained, 1 can become impatient, overly self-protective, or quietly lonely. The pressure to stay strong can make vulnerability feel unsafe, even when connection is exactly what is needed.",
    relationships:
      "In relationships, 1 needs respect, honesty, and room to be fully themselves. It does best with warmth and directness, and it grows when it learns that partnership does not have to mean losing independence.",
    work:
      "In work, 1 prefers ownership, initiative, and visible movement. It thrives in roles where ideas need to be started, shaped, or led rather than endlessly debated.",
    growth:
      "The deeper lesson of 1 is to discover leadership without hardness and confidence without isolation. Its maturity comes from learning that strength and tenderness can live in the same person.",
    spiritual:
      "Spiritually, 1 asks a person to become an original rather than an echo. It points toward courage, integrity, and the quiet discipline of standing in one’s own truth.",
  },
  2: {
    aura: "attuned sensitivity",
    portrait:
      "The energy of 2 is relational, receptive, and emotionally intelligent. It often belongs to people whose path unfolds through listening, responding, sensing nuance, and understanding the subtle dance between self and others.",
    aligned:
      "At its best, 2 creates trust, emotional safety, and harmony. It carries patience, grace, and an ability to hold complexity without forcing a rushed conclusion.",
    shadow:
      "When unsteady, 2 can become overly hesitant, approval-seeking, or quietly resentful. Its desire for peace can sometimes lead to self-erasure or to feelings being swallowed instead of spoken.",
    relationships:
      "In relationships, 2 is deeply loyal and emotionally responsive. It flourishes where tenderness, consistency, and mutual care are present, and it suffers when its sensitivity is treated as weakness.",
    work:
      "In work, 2 shines in collaborative, diplomatic, and detail-aware settings. It often becomes the bridge between people, helping different voices find a shared rhythm.",
    growth:
      "The lesson of 2 is to pair softness with self-respect. Its maturity appears when it learns to stay kind without abandoning clarity or boundaries.",
    spiritual:
      "Spiritually, 2 is invited to trust intuition as a real form of intelligence. It teaches that receptivity is not passivity, but a powerful way of knowing.",
  },
  3: {
    aura: "radiant expression",
    portrait:
      "The energy of 3 is expressive, imaginative, and emotionally colorful. It often appears in people who are meant to create movement through words, ideas, humor, beauty, or the simple gift of making life feel more alive.",
    aligned:
      "When healthy, 3 brings charm, creativity, emotional brightness, and the ability to transform heaviness into meaning. It helps people connect through expression rather than hiding behind control.",
    shadow:
      "When scattered, 3 can become inconsistent, performative, or avoidant of emotional depth. It may stay in motion partly to avoid sitting still with feelings that ask to be fully met.",
    relationships:
      "In relationships, 3 needs delight, openness, and room to be emotionally alive. It does best where affection is verbal, playful, and sincere rather than overly rigid or emotionally cold.",
    work:
      "In work, 3 thrives where communication, design, storytelling, teaching, or presentation matter. It wants to turn raw feeling and abstract ideas into something others can see, hear, or feel.",
    growth:
      "The lesson of 3 is to bring discipline to inspiration. Its power deepens when expression becomes not only bright, but rooted, steady, and emotionally honest.",
    spiritual:
      "Spiritually, 3 points toward joyful creation as a sacred act. It reminds a person that self-expression can be both healing and devotional when it comes from truth.",
  },
  4: {
    aura: "grounded structure",
    portrait:
      "The energy of 4 is practical, stabilizing, and quietly devoted to what lasts. It often belongs to people whose path involves building foundations, creating reliability, and turning scattered energy into real-world form.",
    aligned:
      "At its best, 4 brings endurance, integrity, precision, and calm steadiness. It becomes the force that helps ideas land and helps people trust that something solid is actually being created.",
    shadow:
      "When tense, 4 can become rigid, over-controlling, or overly attached to certainty. Its longing for safety can turn into resistance when life asks it to move before all variables are neatly settled.",
    relationships:
      "In relationships, 4 offers loyalty, consistency, and practical love. It shows care through action and dependability, though it grows when it remembers to show softness as clearly as responsibility.",
    work:
      "In work, 4 thrives in environments where systems, mastery, order, and follow-through matter. It often becomes the person who turns aspiration into a working reality.",
    growth:
      "The lesson of 4 is to let structure serve life rather than control it. Its maturity comes when stability and flexibility begin to work together.",
    spiritual:
      "Spiritually, 4 teaches reverence for disciplined effort. It points toward devotion through craftsmanship, routine, and the humble holiness of building carefully.",
  },
  5: {
    aura: "living movement",
    portrait:
      "The energy of 5 is curious, restless, adaptive, and deeply alive to change. It often appears in people whose path expands through experimentation, reinvention, and learning directly from experience rather than from fixed formulas.",
    aligned:
      "When healthy, 5 brings courage, freshness, versatility, and a willingness to meet life directly. It keeps a person open, inventive, and able to move through transitions with spirit.",
    shadow:
      "When ungrounded, 5 can become impulsive, overstimulated, or resistant to commitment. The hunger for freedom can slide into avoidance when stillness begins to feel too exposing.",
    relationships:
      "In relationships, 5 needs honesty, breathing room, and a feeling of aliveness. It bonds best where there is both intimacy and freedom, rather than emotional possession or rigid control.",
    work:
      "In work, 5 shines where flexibility, communication, exploration, or dynamic problem-solving matter. It thrives when life does not feel static and when curiosity is treated as an asset.",
    growth:
      "The lesson of 5 is to discover that freedom becomes more powerful when it is anchored. Its maturity appears when movement is joined with responsibility instead of running from it.",
    spiritual:
      "Spiritually, 5 asks a person to trust life as a living teacher. It points toward wisdom gained through direct encounter, variety, and honest experience.",
  },
  6: {
    aura: "heart-led responsibility",
    portrait:
      "The energy of 6 is caring, protective, beauty-seeking, and naturally responsive to the needs of others. It often appears in people who are meant to create harmony, offer support, and become a stabilizing presence in family or community life.",
    aligned:
      "At its best, 6 brings warmth, devotion, emotional steadiness, and a refined sense of care. It often becomes the force that nourishes, repairs, and restores balance around it.",
    shadow:
      "When overburdened, 6 can become perfectionistic, over-responsible, or quietly controlling. Its instinct to help can slip into carrying more than is truly theirs to hold.",
    relationships:
      "In relationships, 6 offers loyalty, tenderness, and commitment. It wants to love well and build something enduring, but it grows when it stops equating love with self-sacrifice.",
    work:
      "In work, 6 excels in roles involving care, mentorship, teaching, design, healing, or stewardship. It thrives wherever goodness must be maintained rather than simply imagined.",
    growth:
      "The lesson of 6 is to care deeply without trying to manage everything. Its maturity comes when service is balanced with self-respect and emotional rest.",
    spiritual:
      "Spiritually, 6 points toward love expressed through responsibility. It teaches that beauty, care, and devotion can all become paths of service.",
  },
  7: {
    aura: "inner searching",
    portrait:
      "The energy of 7 is contemplative, perceptive, and drawn toward hidden meaning. It often belongs to people whose lives deepen through study, reflection, solitude, and the desire to understand what lies beneath appearances.",
    aligned:
      "When expressed well, 7 brings discernment, depth, spiritual curiosity, and the ability to think with subtlety. It offers a mind that seeks truth rather than noise and meaning rather than distraction.",
    shadow:
      "When wounded or fatigued, 7 can become withdrawn, guarded, skeptical, or emotionally distant. Its inner complexity can turn into isolation if it stops trusting that it can be understood.",
    relationships:
      "In relationships, 7 needs sincerity, emotional safety, and real depth. It does not flourish in superficial dynamics; it opens slowly, but when it trusts, it seeks profound connection.",
    work:
      "In work, 7 thrives where analysis, wisdom, research, interpretation, or inner depth matter. It is often strongest where understanding is more important than speed.",
    growth:
      "The lesson of 7 is to let wisdom stay connected to life. Its maturity comes when insight is paired with warmth, and solitude becomes a source of clarity rather than separation.",
    spiritual:
      "Spiritually, 7 is one of the clearest numbers of inner seeking. It asks a person to honor mystery, cultivate discernment, and trust the life of the soul as something real.",
  },
  8: {
    aura: "magnetic command",
    portrait:
      "The energy of 8 is strategic, capable, and deeply aware of power, consequence, and material reality. It often appears in people whose path involves learning how to handle responsibility, ambition, and influence with maturity.",
    aligned:
      "At its best, 8 brings authority, resilience, executive clarity, and the ability to move large plans into form. It often becomes the force that can organize chaos and carry weight without collapsing.",
    shadow:
      "When distorted, 8 can become controlling, hardened, overly image-conscious, or driven by fear around loss. The desire for mastery can become exhausting when worth is measured only through achievement.",
    relationships:
      "In relationships, 8 needs respect, loyalty, and emotional honesty beneath the outer strength. It softens beautifully when it feels safe enough to stop performing competence all the time.",
    work:
      "In work, 8 thrives in leadership, entrepreneurship, management, finance, negotiation, or any field requiring clear responsibility. It likes building results that can be felt in the real world.",
    growth:
      "The lesson of 8 is to humanize power. Its maturity appears when ambition becomes aligned with wisdom, generosity, and inner steadiness rather than control alone.",
    spiritual:
      "Spiritually, 8 asks a person to use worldly capacity in service of a deeper ethic. It teaches stewardship, accountability, and the disciplined use of influence.",
  },
  9: {
    aura: "compassionate vastness",
    portrait:
      "The energy of 9 is idealistic, feeling-rich, and aware of the broader human story. It often belongs to people who are meant to live with emotional breadth, moral imagination, and a strong instinct toward service, meaning, and completion.",
    aligned:
      "When healthy, 9 brings empathy, wisdom, forgiveness, and an ability to hold the bigger picture. It helps a person connect personal experience to something more universal and humane.",
    shadow:
      "When unbalanced, 9 can become overextended, emotionally flooded, or trapped in patterns of rescuing. Its compassion can turn heavy when it forgets that boundaries are part of love too.",
    relationships:
      "In relationships, 9 is generous, soulful, and deeply feeling. It wants emotional significance, shared values, and a sense that love is connected to growth rather than mere comfort.",
    work:
      "In work, 9 thrives in healing, guidance, teaching, advocacy, creativity, or service-oriented paths. It is often called toward work that uplifts, reforms, or gives something meaningful back.",
    growth:
      "The lesson of 9 is to serve without dissolving the self. Its maturity comes through grounded compassion, wise endings, and the ability to release what no longer belongs.",
    spiritual:
      "Spiritually, 9 points toward surrender, mercy, and completion. It invites a person to become large-hearted without becoming undefined.",
  },
  11: {
    aura: "electric intuition",
    portrait:
      "The energy of 11 is heightened, visionary, and unusually sensitive to unseen currents. It often appears in people whose lives involve awakening, inspiration, and the challenge of translating subtle perception into something grounded and helpful.",
    aligned:
      "At its best, 11 brings insight, inspiration, originality, and a rare emotional voltage. It can light up possibilities that others sense only dimly and help turn intuition into guidance.",
    shadow:
      "When dysregulated, 11 can become anxious, overstimulated, inconsistent, or self-doubting. Its sensitivity is powerful, but it needs grounding or it can become overwhelmed by its own intensity.",
    relationships:
      "In relationships, 11 needs emotional honesty, spiritual respect, and a sense of energetic safety. It bonds deeply but can retreat when life feels too noisy or dismissive of what it senses.",
    work:
      "In work, 11 shines in creative, spiritual, communicative, or visionary roles where inspiration matters. It often does its best work when it can bridge insight and lived reality.",
    growth:
      "The lesson of 11 is to ground revelation in rhythm. Its maturity comes when sensitivity becomes a disciplined gift instead of a source of nervous scattering.",
    spiritual:
      "Spiritually, 11 is often read as a number of illumination. It asks a person to become a clear channel rather than a flooded one.",
  },
  22: {
    aura: "vision made tangible",
    portrait:
      "The energy of 22 is expansive, capable, and unusually suited to turning a large vision into durable form. It often appears in people whose life path involves translating ideals into systems, structures, or contributions that outlast immediate moods.",
    aligned:
      "At its best, 22 brings scale, strategic clarity, discipline, and a rare ability to build for the long term. It can unite imagination with execution in a way that feels both ambitious and practical.",
    shadow:
      "When pressured, 22 can become overwhelmed, self-doubting, hyper-responsible, or afraid of the weight of its own potential. It sometimes swings between grand vision and paralysis when the task feels too large.",
    relationships:
      "In relationships, 22 needs steadiness, mutual respect, and faith in what is being built together. It values substance and commitment more than performative romance.",
    work:
      "In work, 22 thrives where planning, systems, large projects, leadership, and long-term impact matter. It is often called to build something real rather than merely talk about possibility.",
    growth:
      "The lesson of 22 is to work patiently with power. Its maturity appears when vision is broken into faithful steps and the future is built without self-crushing pressure.",
    spiritual:
      "Spiritually, 22 speaks of sacred construction. It asks a person to remember that practical achievement can itself become a form of service.",
  },
  33: {
    aura: "healing devotion",
    portrait:
      "The energy of 33 is heart-centered, protective, and deeply responsive to suffering. It often belongs to people whose lives are shaped by teaching, healing, moral care, and the challenge of loving in a way that uplifts without overextending the self.",
    aligned:
      "When expressed beautifully, 33 brings compassion, tenderness, integrity, and a gift for helping others feel seen. It often has a naturally mentoring quality and a desire to turn pain into wisdom or comfort.",
    shadow:
      "When overburdened, 33 can become drained, self-sacrificing, overidentified with others’ pain, or quietly resentful. The impulse to heal can become unsustainable if it is not paired with boundaries.",
    relationships:
      "In relationships, 33 is warm, loyal, and deeply giving. It seeks soulfulness, emotional maturity, and a sense that love is part of a shared path of growth and repair.",
    work:
      "In work, 33 shines in healing, teaching, caregiving, guidance, and service. It often does best where emotional intelligence and moral presence matter as much as skill.",
    growth:
      "The lesson of 33 is to care without depletion. Its maturity comes through protecting its own life force while continuing to love generously.",
    spiritual:
      "Spiritually, 33 is often associated with compassionate service. It asks a person to become a steady source of healing rather than a person consumed by everyone else’s pain.",
  },
}

function getArchetype(number: number): Archetype {
  return ARCHETYPES[number] || ARCHETYPES[1]
}

export function buildCardCopy(item: NumerologyNumber): CardCopy {
  const archetype = getArchetype(item.number)

  if (item.key === "life_path") {
    return {
      intro:
        "Your Life Path is the riverbed of the reading. It describes the deeper road your life keeps returning to, the lessons that mature you, and the kind of wisdom experience is trying to carve into you over time.",
      body: `${archetype.portrait} ${archetype.spiritual}`,
      alignedTitle: "When You Are In Rhythm",
      alignedBody: archetype.aligned,
      growthTitle: "What Life Is Teaching You",
      growthBody: `${archetype.shadow} ${archetype.growth}`,
    }
  }

  if (item.key === "destiny") {
    return {
      intro:
        "Your Destiny number shows how your gifts naturally want to take shape in the outer world. It is less about private feeling and more about contribution, expression, and the kind of imprint your energy tends to leave behind.",
      body: `${archetype.work} ${archetype.aligned}`,
      alignedTitle: "How Your Gifts Become Visible",
      alignedBody: archetype.work,
      growthTitle: "What Refines Your Contribution",
      growthBody: `${archetype.shadow} ${archetype.growth}`,
    }
  }

  if (item.key === "soul_urge") {
    return {
      intro:
        "Your Soul Urge points to the emotional truth underneath the surface. It reveals what your heart quietly wants, what nourishes you at a deep level, and what kind of inner life feels most honest to your nature.",
      body: `${archetype.portrait} ${archetype.relationships}`,
      alignedTitle: "What Your Heart Moves Toward",
      alignedBody: archetype.spiritual,
      growthTitle: "What Happens When It Is Unmet",
      growthBody: `${archetype.shadow} ${archetype.growth}`,
    }
  }

  if (item.key === "personality") {
    return {
      intro:
        "Your Personality number shapes the tone people often feel first. It does not describe your entire being, but it does color your social presence, your visible style, and the energetic doorway through which others tend to meet you.",
      body: `${archetype.relationships} ${archetype.aligned}`,
      alignedTitle: "What People Often Feel Around You",
      alignedBody: archetype.relationships,
      growthTitle: "How This Energy Can Misfire",
      growthBody: `${archetype.shadow} ${archetype.growth}`,
    }
  }

  if (item.key === "birthday") {
    return {
      intro:
        "Your Birthday number is a secondary influence, but it often adds a vivid tone to your style. It can describe a natural gift, a recurring flavor in your personality, or a familiar way your energy enters experience.",
      body: `${archetype.portrait} ${archetype.aligned}`,
      alignedTitle: "A Natural Strength You Carry",
      alignedBody: archetype.aligned,
      growthTitle: "Its Less Integrated Side",
      growthBody: archetype.shadow,
    }
  }

  return {
    intro:
      "Your Attitude number describes the immediate way you tend to approach life, especially at first contact. It often colors your first response to new people, fresh situations, and the tone with which you enter experience.",
    body: `${archetype.portrait} ${archetype.work}`,
    alignedTitle: "The Energy You Lead With",
    alignedBody: archetype.aligned,
    growthTitle: "What Helps It Mature",
    growthBody: `${archetype.shadow} ${archetype.growth}`,
  }
}

export function buildReadingSummary(
  fullName: string,
  numbers: Partial<Record<NumerologyKey, NumerologyNumber>>
): string[] {
  const lifePath = numbers.life_path
  const destiny = numbers.destiny
  const soulUrge = numbers.soul_urge
  const personality = numbers.personality
  const birthday = numbers.birthday
  const attitude = numbers.attitude

  if (!lifePath || !destiny || !soulUrge || !personality || !birthday || !attitude) {
    return []
  }

  const life = getArchetype(lifePath.number)
  const dest = getArchetype(destiny.number)
  const soul = getArchetype(soulUrge.number)
  const outer = getArchetype(personality.number)
  const birth = getArchetype(birthday.number)
  const attitudeArc = getArchetype(attitude.number)

  return [
    `${fullName}, your reading is anchored by Life Path ${lifePath.number}, which carries the feeling of ${life.aura}. That suggests a life shaped less by surface momentum and more by the gradual unfolding of ${lifePath.keywords.join(", ")}. Destiny ${destiny.number} adds the note of ${dest.aura}, which means your gifts are not only meant to be felt inwardly, but expressed outwardly through the way you contribute, create, guide, or build in the world.`,
    `Underneath that outer contribution, Soul Urge ${soulUrge.number} shows that your inner life is seeking ${soul.aura}, while Personality ${personality.number} gives others an immediate sense of ${outer.aura}. Birthday ${birthday.number} adds a natural streak of ${birth.aura}, and Attitude ${attitude.number} shapes the first tone with which you meet life. Together, these numbers suggest a person whose path is not one-dimensional, but layered: part destiny, part temperament, part longing, and part lesson.`,
  ]
}

export function buildInsightSections(
  numbers: Partial<Record<NumerologyKey, NumerologyNumber>>
): InsightSection[] {
  const lifePath = numbers.life_path
  const destiny = numbers.destiny
  const soulUrge = numbers.soul_urge
  const personality = numbers.personality
  const birthday = numbers.birthday
  const attitude = numbers.attitude

  if (!lifePath || !destiny || !soulUrge || !personality || !birthday || !attitude) {
    return []
  }

  const life = getArchetype(lifePath.number)
  const dest = getArchetype(destiny.number)
  const soul = getArchetype(soulUrge.number)
  const outer = getArchetype(personality.number)
  const birth = getArchetype(birthday.number)
  const att = getArchetype(attitude.number)

  return [
    {
      title: "Your inner life and outer presence",
      body: `Soul Urge ${soulUrge.number} suggests that your private emotional world is drawn toward ${soul.aura}. In simple terms, your heart wants meaning, nourishment, and self-recognition in that style. Yet Personality ${personality.number} means others may first meet the ${outer.aura} side of you. This creates an important distinction between what you feel deeply inside and what the world perceives first. The more these two layers are allowed to speak to each other rather than compete, the more integrated and magnetic your presence becomes.`,
    },
    {
      title: "The work your life wants to do through you",
      body: `Life Path ${lifePath.number} shows the road that is shaping you, while Destiny ${destiny.number} shows the form your gifts want to take in visible life. In your case, that means a path flavored by ${lifePath.keywords.join(", ")} expressing itself through the outer style of ${destiny.keywords.join(", ")}. Often this kind of pattern suggests that your life is not only about personal growth, but about translating inner development into something useful, generous, beautiful, wise, or stabilizing for others.`,
    },
    {
      title: "How your smaller numbers quietly support the whole reading",
      body: `Birthday ${birthday.number} adds an extra current of ${birth.aura}, which can show up as a natural talent or an instinctive way of moving through life. Attitude ${attitude.number} adds the tone of ${att.aura}, shaping how you step into new chapters, conversations, and first impressions. These influences may not be the backbone of the reading, but they often explain why your energy lands the way it does in everyday life.`,
    },
    {
      title: "The deeper invitation beneath the numbers",
      body: `${life.growth} ${dest.growth} ${soul.growth} Read together, these numbers suggest that your growth does not come from becoming someone else, but from refining what is already strongest in you. The invitation is not to force a new identity, but to live your existing nature with more consciousness, steadiness, and trust.`,
    },
  ]
}

export function buildOrientationPanels(
  numbers: Partial<Record<NumerologyKey, NumerologyNumber>>
): InsightSection[] {
  const destiny = numbers.destiny
  const soulUrge = numbers.soul_urge
  const personality = numbers.personality
  const lifePath = numbers.life_path

  if (!lifePath || !destiny || !soulUrge || !personality) {
    return []
  }

  const dest = getArchetype(destiny.number)
  const soul = getArchetype(soulUrge.number)
  const outer = getArchetype(personality.number)
  const life = getArchetype(lifePath.number)

  return [
    {
      title: "In relationships",
      body: `${soul.relationships} ${outer.relationships} With Life Path ${lifePath.number} in the background, your relationships tend to become a place where your deeper life lessons are made visible rather than avoided.`,
    },
    {
      title: "In work and contribution",
      body: `${dest.work} ${life.work} This suggests that work becomes most meaningful when it feels aligned not only with competence, but with a deeper sense of purpose and right direction.`,
    },
    {
      title: "In times of stress",
      body: `${life.shadow} ${soul.shadow} ${outer.shadow} These patterns are not flaws so much as signals that your energy needs rebalancing, rest, honesty, or a return to what is truly essential.`,
    },
  ]
}
