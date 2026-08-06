---
id: emotion-kb
aliases: [پایگاه دانش هیجان, emotion knowledge base, intuition KB, collective feeling]
tags: [ادبیات, #reference, هیجان, شهود, خودآگاهی]
source: conversation-archive
related: ["[[سنتز-SOG-جامع]]", "[[MOC-خودتنظیم‌گری-و-خودآگاهی]]", "[[Delta-self]]", "[[E-shadow]]"]
---

# MASTER KNOWLEDGE BASE — Human Emotion, Intuition & Collective Feeling### v1.0 · Breadth-first structured map · Compiled 2026-07-10> **What this is.** A structured, computationally-ingestible map of the major *serious* theories, models, traditions, evidence, and open debates across the science and philosophy of affect, intuition, and collective feeling. Optimized for information density and graph/DB ingestion, not narrative reading.
>
> **What this is NOT.** Exhaustive. True exhaustiveness here is a database built over many passes (thousands of nodes). This is a **v1 scaffold** covering the pivotal theories per domain, with hooks to extend. Where a whole sub-literature is compressed to one row, that is a deliberate lossy summary, flagged where it matters.
>>
> **Operating principles (enforced throughout):** (1) preserve competing hypotheses — no forced consensus; (2) separate *evidence* from *speculation*; (3) mark uncertainty explicitly; (4) distinguish empirical claims from philosophical ones.---## 0 · How to read this (coding scheme)

**Evidence level** — strength of the empirical base *for the theory's core claim*:

| Code | Meaning |
|---|---|
| `E4` | Robust — convergent, replicated, meta-analytic support |
| `E3` | Moderate — multiple supporting studies, some contested |
| `E2` | Mixed/Weak — limited or conflicting evidence |
| `E1` | Contested/Failed — largely disputed or failed key replications |
| `E0` | Non-empirical — philosophical/conceptual; not settleable by current experiment |

**Confidence** (`C`) — *my* confidence that the row accurately represents current scholarly state: `Hi` / `Md` / `Lo`.**Provenance** — `[V]` verified via web search in this session (2026-07); `[K]` from training knowledge, not re-verified this session; `[V/K]` mixed. Treat `[K]` rows as "expert-summary, spot-check before citing."

**Status** — `Active` / `Foundational` (historically pivotal, partly superseded) / `Contested` / `Discredited`.

**Relationship vocabulary** (for the graph, §7): `SUPPORTS · CONTRADICTS · EXTENDS · SUBSUMES · SPECIAL_CASE_OF · OPERATIONALIZES · MEASURES · GROUNDS · GROUNDED_IN · COMPETES_WITH · PRECEDES · CONTESTED_BY · PROPOSED_BASIS_FOR · APPLIES · REGULATED_BY · ANALOG_OF`.

---## 1 · Ontology / Taxonomy of the field### 1.1 Core construct disambiguation (the terms are NOT synonyms)| Construct | Working definition | Timescale | Object/aboutness | Consciously felt? |
|---|---|---|---|---|
| **Affect / core affect** | Primitive valence × arousal state | Continuous | Not necessarily object-directed | Sometimes |
| **Emotion** | Coordinated multi-component episode (appraisal + physiology + action tendency + expression + feeling) directed at something | Seconds–minutes | Object-directed | Usually |
| **Feeling** | The conscious/experiential component of affect or emotion | Seconds–minutes | May be diffuse | By definition |
| **Mood** | Diffuse, low-intensity, longer affective background | Hours–days | Objectless | Backgrounded |
| **Emotional trait / temperament** | Dispositional tendency toward affective states | Stable | — | — || **Sentiment / attitude** | Evaluative disposition toward a target | Stable | Object-directed | Not per se |
| **Qualia / phenomenal experience** | The "what-it-is-like" character of a state | Instant | — | By definition |
| **Instinct** | Innate, species-typical behavioral disposition | — | Trigger-bound | No |
| **Intuition / "gut feeling"** | Fast judgment/impression without accessible deliberate reasoning | Instant | Decision-directed | Output felt, process not |
| **Empathy** | Sharing/inferring another's affective state | Seconds | Other-directed | Varies |
| **Collective / shared emotion** | Convergent affective state across individuals via interaction | Varies | Group-level | Individually |> **Key fault line #1:** Are emotions *natural kinds* (discrete, evolved, biologically given — "fingerprints") or *constructed categories* (assembled from core affect + concepts + context)? This single axis reorganizes most of the field (see §5 debate D1).
>
> **Key fault line #2:** Is feeling *perception of the body* (James → Damasio → Seth) or *central/cognitive constitution*? (see D4).### 1.2 Domain map (the 12 clusters catalogued in §2)```
A  Classical psychological theories of emotion
B  Affective neuroscience / biology of emotion
C  Structure & measurement (discrete vs dimensional vs constructed)
D  Predictive / computational brain (Bayesian, FEP, active inference, RL)
E  Consciousness / qualia / subjective experience
F  Intuition, dual-process, heuristics, expertise
G  Empathy / intersubjectivity
H  Collective emotion / contagion / synchrony
I  Collective intelligence / crowds / swarms
J  Cultural / evolutionary / semiotic / cybernetic / information-theoretic
K  Affective computing / Emotion AI
L  Behavioral economics / neuroeconomics of affect
+  Emotion regulation (cross-cuts A–L)
+  Cross-tradition map (Greek / Persian-Islamic / Indian / Chinese / Buddhist / Stoic)
```

---## 2 · Theory catalogue (compact rows)

> Format: **Theory** — Author(s), Year · *core claim* · **For** · **Against/limits** · `Status · E · C · prov`### Cluster A — Classical psychological theories of emotion| Theory | Core claim | For | Against / limits | Coding |
|---|---|---|---|---|
| **James–Lange** (W. James 1884; C. Lange 1885) | Bodily/physiological response *precedes and constitutes* emotion; feeling = perception of body change | Interoception & embodiment revival; Damasio | Cannon: visceral responses too slow, undifferentiated; sham rage in decorticate animals | `Foundational · E2 · Md · [K]` |
| **Cannon–Bard** (Cannon 1927; Bard 1928) | Bodily and emotional experience arise *simultaneously* via thalamus/hypothalamus | Sham-rage studies | Oversimplified neuroanatomy | `Foundational · E2 · Md · [K]` || **Two-factor / cognitive-arousal** (Schachter & Singer 1962) | Emotion = undifferentiated arousal + cognitive label | Misattribution of arousal (Dutton–Aron bridge, 1974) | Weak/mixed direct replication; arousal not fully undifferentiated | `Foundational · E2 · Md · [K]` |
| **Appraisal theory** (Arnold 1960; Lazarus 1966/91; Roseman; Scherer CPM; OCC — Ortony-Clore-Collins 1988) | Emotions arise from cognitive *appraisal* of events vs goals/values | Robust appraisal→emotion mappings; OCC dominant in AI agents | Some responses appear pre-cognitive (Zajonc) | `Active · E3 · Hi · [K]` || **Affect primacy** (Zajonc 1980, "preferences need no inferences") | Affect can occur *before/without* cognition | Mere-exposure effect; subliminal affective priming | Overstated as exclusive route | `Active · E3 · Hi · [K]` |
| **Facial feedback hypothesis** (Tomkins 1962; Strack et al. 1988) | Facial muscle configuration modulates felt emotion | Coles et al. 2019 meta: small real effect | Wagenmakers et al. 2016 many-labs *failed* Strack replication | `Contested · E2 · Md · [V/K]` |
| **Broaden-and-build** (Fredrickson 1998/2001) | Positive emotions broaden thought–action repertoires, build resources | Some experimental support | "Positivity ratio" (Losada) sub-claim **debunked/retracted** (Brown, Sokal & Friedman 2013) | `Active(partial) · E2 · Md · [K]` |### Cluster B — Affective neuroscience / biology| Theory | Core claim | For | Against / limits | Coding |
|---|---|---|---|---|
| **Papez circuit** (1937) | Dedicated cortico-limbic loop for emotion | Anatomical influence | Incomplete | `Foundational · E2 · Md · [K]` |
| **Limbic system / Triune brain** (MacLean 1949/1990) | "Reptilian/paleomammalian/neomammalian" brain layers; emotion = limbic | Heuristic popularity | Triune evolutionary account **inaccurate/discredited**; "limbic system" boundary fuzzy | `Discredited(triune) · E1 · Hi · [K]` || **Fear/defense circuits → survival circuits** (LeDoux 1996; 2015+) | Amygdala-centered threat circuits ("low/high road"); LeDoux *later* separates nonconscious *defensive responses* from conscious *feelings of fear* | Strong rodent fear-conditioning data | Human amygdala evidence indirect; "fear" ≠ the circuit (LeDoux's own revision) | `Active · E3 · Hi · [K]` |
| **Somatic Marker Hypothesis** (Damasio 1994; Bechara IGT) | Bodily/affective "markers" bias decision under uncertainty; feelings = perception of body state | vmPFC-lesion decision deficits; anticipatory SCRs in Iowa Gambling Task | Maia & McClelland 2004: subjects had *explicit* knowledge before "hunch"; IGT design confounds | `Influential/Contested · E2 · Md · [K]` || **Affective Neuroscience / primary-process emotions** (Panksepp 1998) | 7 subcortical systems: SEEKING, RAGE, FEAR, LUST, CARE, PANIC/GRIEF, PLAY; cross-species | Homologous subcortical circuits; deep-brain stimulation evokes affect; rat 50-kHz "laughter"/play | Constructionists dispute discrete affect programs; naming/anthropomorphism | `Active · E3 · Hi · [K]` |
| **Emotion–cognition integration** (Pessoa 2008) | No clean emotion/cognition split; amygdala as network hub | Connectivity/fMRI | Framework, not point prediction | `Active · E3 · Hi · [K]` || **Neurochemistry of affect** (dopamine RPE — Schultz; cortisol; testosterone; serotonin; oxytocin) | Neuromodulators bias affective thresholds/tendencies | Strong for dopamine reward-prediction-error | Oxytocin "love/trust hormone" **overhyped**, many failed replications; effects are biasing, not deterministic | `Mixed · E2–E4 · Md · [K]` |### Cluster C — Structure & measurement of emotion| Theory | Core claim | For | Against / limits | Coding |
|---|---|---|---|---|
| **Basic/Discrete Emotion Theory** (Darwin 1872; Tomkins; Ekman & Friesen 1971; FACS 1978; Izard) | Small set of universal, evolved, discrete emotions with distinct facial signatures | Cross-cultural recognition-above-chance; FACS; extended by Keltner/Cowen/Cordaro (>20 categories) | **Barrett et al. 2019 [V]:** face→emotion mappings lack *reliability, specificity, generalizability*; cultural variation (Gendron, Roberson — Himba); forced-choice artifacts | `Contested · E2 · Md · [V]` |
| **Circumplex / Core Affect** (Russell 1980; Russell & Barrett 1999) | All affect maps onto *valence × arousal* | Robust factor structure; ubiquitous | Loses category-specific info | `Active · E3 · Hi · [K]` || **PANAS / PA–NA** (Watson & Tellegen 1988) | Two independent dims: Positive & Negative Affect | Widely validated instrument | Debate w/ valence-arousal framing | `Active · E3 · Hi · [K]` |
| **PAD** (Mehrabian & Russell) | Pleasure–Arousal–Dominance 3-D space | Used in HCI/affective computing | — | `Active · E3 · Md · [K]` |
| **Plutchik's wheel** (1980) | 8 primary bipolar emotions; blends & intensities; evolutionary | Intuitive heuristic | Weak empirical grounding vs dimensional/discrete | `Popular · E2 · Md · [K]` |
| **Component Process Model** (Scherer 1984–2009) | Emotion = transient *synchronization* of 5 components via sequential appraisal checks | Structured, testable appraisal predictions | Complexity; partial tests | `Active · E3 · Hi · [K]` || **Semantic space of emotion** (Cowen & Keltner 2017) | ~27 distinct emotion categories bridged by gradients (not 6 discrete islands) | Large data-driven studies | Method/sampling debates | `Active · E3 · Md · [K]` |
| **Theory of Constructed Emotion** (Barrett 2006 "conceptual act"; 2017) | Emotions are *not* natural kinds; brain constructs instances from core affect + interoception + concepts/language + prediction; situated, culturally learned | Variability data; absence of consistent biomarkers; concept/language effects | Under-weights conserved circuits (Panksepp/Ekman camps); *falsifiability* debated | `Active(major) · E3(variability)/E2(strong mechanism) · Md · [V]` |### Cluster D — Predictive / computational brain| Theory | Core claim | For | Against / limits | Coding |
|---|---|---|---|---|
| **Bayesian brain / predictive coding** (Helmholtz; Rao & Ballard 1999; Knill & Pouget 2004) | Perception = probabilistic inference minimizing prediction error | Broad neural/behavioral support | Scope of literal implementation debated | `Active · E3 · Hi · [K]` |
| **Free Energy Principle / Active Inference** (Friston 2006–2010+) | Agents minimize variational free energy (bound on surprise); perception & action both reduce prediction error; affect ≈ inference on internal state/precision | Unifying; generative models; some operationalization | Criticized as near-*unfalsifiable* / too general; heavy formalism | `Active · E2(as grand claim)/E0-adjacent · Md · [K]` || **Interoceptive inference / "beast machine"** (Seth 2013+; Seth & Friston 2016; EPIC — Barrett & Simmons 2015) | Emotions/feelings = predictive models of *interoceptive* (bodily) signals; self = "controlled hallucination" | Interoception↔emotion links (heartbeat detection; Garfinkel interoception dimensions) | Interoceptive-accuracy measures noisy; causal direction open | `Active · E3(interoception link) · Md · [K]` |
| **Dopamine reward-prediction error** (Montague, Dayan, Schultz 1997) | Phasic dopamine encodes RPE = reward − expectation | Very strong electrophysiology | Not a full theory of emotion | `Active · E4 · Hi · [K]` || **Mood as momentum of reward** (Eldar et al. 2016) | Mood ≈ integrated recent RPEs; biases perception of subsequent outcomes | Computational + empirical support | Newer, scope limited | `Active · E2 · Md · [K]` |
| **Affect as expected-value / free-energy / learning progress** (Joffily & Coricelli; Schmidhuber compression-progress; Oudeyer & Kaplan curiosity) | Valence tracks rate-of-change of prediction error / model improvement; curiosity = intrinsic reward for learning progress | Elegant; works in agents/robots | Mostly modeling; human tests partial | `Active · E2 · Md · [K]` |### Cluster E — Consciousness / qualia / subjective experience| Theory | Core claim | For | Against / limits | Coding |
|---|---|---|---|---|
| **Hard problem** (Chalmers 1995) | Explanatory gap: why is there *something it is like*? | Frames the debate | Not empirical; eliminativists (Dennett) deny the framing | `Philosophical · E0 · Hi · [K]` |
| **Qualia / knowledge argument** (Nagel 1974 "bat"; Jackson 1982 "Mary") | Subjective character is irreducible to physical facts | Strong intuition pump | Physicalist rebuttals; Jackson himself later recanted | `Philosophical · E0 · Hi · [K]` || **Global (Neuronal) Workspace** (Baars 1988; Dehaene & Changeux) | Consciousness = global *broadcast/ignition* of information for access | Neural signatures of access (late ignition, P3b); COGITATE partial support [V] | Explains *access*, arguably not *phenomenal* consciousness | `Leading/Active · E3 · Hi · [V/K]` |
| **Integrated Information Theory** (Tononi 2004→v4.0; Koch) | Consciousness = integrated information **Φ**; axioms→postulates; near-*panpsychism* | Perturbational Complexity Index (PCI) clinically useful; some COGITATE support | **2023 "pseudoscience" open letter, 124 signatories [V]**; non-uniqueness (Hanson & Walker); unfolding argument (Doerig 2019); Φ incomputable at scale | `Leading-but-embattled · E1(as full theory)/E2(PCI) · Hi · [V]` || **Higher-Order Theories** (Rosenthal; Lau & Brown) | A state is conscious iff represented by a higher-order state | Metacognition data | Circularity/targetless-HOT objections | `Active · E2 · Md · [K]` |
| **Recurrent Processing Theory** (Lamme) | Local recurrent processing suffices for phenomenal consciousness | Visual neuroscience | Competes w/ GNWT on "no-report" | `Active · E2 · Md · [K]` |
| **Attention Schema Theory** (Graziano 2013) | Consciousness = brain's schematic model of its own attention | Parsimonious; engineering-friendly | Limited direct tests | `Active · E2 · Md · [K]` || **Enactivism / autopoiesis / sensorimotor** (Varela, Thompson & Rosch 1991; O'Regan & Noë 2001; Colombetti 2014 affective) | Experience is *constituted* by embodied action & world-coupling; life–mind continuity; affect is bodily-enacted | Coherent alternative to representationalism | Hard to operationalize; "constitution vs causation" disputed | `Active · E0/E2 · Md · [K]` |
| **Embodied/grounded cognition** (Lakoff & Johnson; Barsalou; Clark extended mind) | Concepts (incl. emotion concepts) grounded in sensorimotor systems | Some embodiment effects | Several priming/embodiment effects **failed to replicate** | `Active/Contested · E2 · Md · [K]` |### Cluster F — Intuition / dual-process / heuristics / expertise| Theory | Core claim | For | Against / limits | Coding |
|---|---|---|---|---|
| **Dual-process (System 1 / 2)** (Sloman 1996; Stanovich; Kahneman 2011; Epstein CEST) | Fast automatic intuitive vs slow deliberate reasoning | Broad phenomena | "Two systems" too clean (Melnikoff & Bargh 2018 "mythical number two"); some pillars (ego depletion, priming) hit by replication crisis | `Active(reframed) · E2 · Md · [K]` |
| **Heuristics & biases** (Tversky & Kahneman 1974) | Intuition uses heuristics (availability, representativeness, anchoring) → systematic bias | Robust core effects | A minority of specific effects contested | `Active · E4(core) · Hi · [K]` || **Fast-and-frugal / ecological rationality** (Gigerenzer & ABC; Goldstein 1996; "gut feelings" 2007) | Simple heuristics are *adaptive* & often near-optimal in real environments (recognition heuristic, take-the-best) | Field & simulation evidence; less-is-more effects | Boundary conditions; debate w/ Kahneman on flaw-vs-feature | `Active · E3 · Hi · [K]` |
| **Recognition-Primed Decision / Naturalistic DM** (Klein 1998) | Expert intuition = rapid pattern-matching from experience | Field studies (firefighters, nurses, military) | Requires valid, high-feedback domains | `Active · E3 · Hi · [K]` || **Conditions for intuitive expertise** (Kahneman & Klein 2009) | Intuition is trustworthy iff environment is *regular/predictable* AND offers *rapid, valid feedback* | Reconciles Klein–Kahneman | Domain-specific | `Active · E3 · Hi · [K]` |
| **Intuition as implicit/statistical learning** (Reber; Lewicki) | Much "intuition" = nonconscious acquisition of environmental regularities → *pattern recognition mistaken for magic* | Artificial-grammar & sequence learning | Extent of "nonconscious" contested | `Active · E3 · Hi · [K]` || **Unconscious Thought Theory** (Dijksterhuis & Nordgren 2006) | Complex decisions improve after distraction ("deliberation-without-attention") | Original studies | **Multiple failed replications & null meta** (Nieuwenstein et al. 2015) | `Contested/Not-replicated · E1 · Hi · [K]` |
| **Thin-slicing** (Ambady & Rosenthal 1992; Gladwell popularization) | Accurate judgments from brief exposure | Some predictive validity | Popular overreach; accuracy domain-bound | `Mixed · E2 · Md · [K]` |### Cluster G — Empathy / intersubjectivity| Theory | Core claim | For | Against / limits | Coding |
|---|---|---|---|---|
| **Perception–Action Model** (Preston & de Waal 2002) | Empathy = shared representations on a continuum: contagion → concern → perspective-taking | Comparative + developmental data | Mechanistic detail | `Active · E3 · Hi · [K]` |
| **Empathy–Altruism Hypothesis** (Batson 1991) | Empathic concern produces *genuine* altruism, not egoism | Experiments dissociating empathy from self-benefit | Egoistic reinterpretations persist | `Active-debate · E2 · Md · [K]` || **Simulation vs Theory-theory of mind** (Goldman; Gopnik) + mentalizing net (mPFC, TPJ; Frith & Frith) | We understand others by simulating vs by folk theory | Robust mentalizing network | Which mechanism dominates: open | `Active · E3(network) · Hi · [K]` |
| **Mirror neurons** (di Pellegrino/Rizzolatti/Gallese 1992) | Neurons firing for executed & observed action; proposed basis for empathy/imitation/language | Macaque single-unit; some human (Mukamel 2010) | **Hickok 2009/2014**: action-*understanding*/empathy claims overextended; human evidence indirect; associative-learning account (Heyes) | `Real-but-hyped · E2(existence)/E1(empathy claim) · Md · [K]` || **Compassion vs empathic distress** (Singer & Klimecki; Zaki) | Affective empathy ≠ compassion; training shifts the balance | Meditation/training fMRI | Effect sizes modest | `Active · E3 · Md · [K]` |
| **Primitive emotional contagion** (Hatfield, Cacioppo & Rapson 1993) | Automatic mimicry + afferent feedback → convergence of emotion | Foundational; broad | Small effects in field; see H | `Active · E3 · Hi · [K]` |### Cluster H — Collective emotion / contagion / synchrony| Theory | Core claim | For | Against / limits | Coding |
|---|---|---|---|---|
| **Crowd psychology** (Le Bon 1895; Tarde imitation; McDougall "group mind") | Crowds form an emergent, contagious, "irrational" collective mind | Historically foundational | Le Bon's literal "group mind" **superseded** by **Elaborated Social Identity Model** (Reicher, Drury) — crowd behavior is norm-structured, not mindless | `Foundational→Superseded · E1(literal)/E3(ESIM) · Md · [K]` |
| **Collective effervescence** (Durkheim 1912) | Shared ritual generates collective emotional energy & solidarity | Enduring sociological framework; → Interaction Ritual Chains (Collins 2004) | Hard to measure directly | `Framework · E2 · Md · [K]` || **Macro-scale emotional contagion (online)** (Kramer, Guillory & Hancock 2014) | Reducing positive/negative content in feeds shifts users' *textual* affect — contagion without nonverbal cues | N=689,003 experiment; statistically real | **Effect size tiny**; LIWC validity for status updates; **major ethics controversy** (no informed consent; editorial expression of concern) | `Contested-magnitude/ethics · E2 · Hi · [V]` |
| **Complex contagion** (Centola & Macy 2007) | Behaviors/affect (unlike disease) often need *social reinforcement* from multiple contacts to spread | Network experiments (Centola 2010) | Boundary conditions | `Active · E3 · Hi · [V/K]` || **Network contagion of affect** (Fowler & Christakis 2008 happiness; Cacioppo 2009 loneliness) | Happiness/loneliness spread to ~3 degrees of separation | Framingham longitudinal correlations | **Homophily/shared-environment confound** (Shalizi & Thomas 2011: generically confounded; Cohen-Cole & Fletcher: "height/acne" also look contagious; Lyons); authors' own sensitivity analysis admits happiness/loneliness *less* robust than obesity/smoking | `Contested · E1 · Hi · [V]` |
| **Group affect / affective tone** (Barsade 2002 "ripple effect"; George; EASI — Van Kleef) | Emotions converge in teams; emotions act as *social information* shaping others | Lab + org studies | Field generalization | `Active · E3 · Hi · [K]` || **Behavioral mimicry / chameleon effect** (Chartrand & Bargh 1999) | Nonconscious mimicry increases affiliation | Core mimicry replicates | Some downstream social effects overstated | `Active · E2 · Md · [K]` |
| **Physiological & inter-brain synchrony** (Hasson brain-to-brain coupling; Dumas; hyperscanning; couple/team EDA-HR synchrony) | Interacting people show coupled physiology/neural activity | Growing correlational evidence | **Artifact risk** (shared stimulus ≠ true coupling); causality open | `Active-frontier · E2 · Lo–Md · [K]` |
| **Moral/emotional contagion in networks** (Brady et al. 2017; Crockett 2017; "MAD" model) | Moral-emotional language amplifies diffusion of outrage/content | Large Twitter datasets | Platform-specific; correlational | `Active · E3 · Md · [K]` || **Behavioral contagion at scale** (Bond et al. 2012) | A single social-message manipulation changed *real voting* of ~61M people & their friends | Large randomized field experiment (Nature) | Small per-person effect; one platform | `Active · E3 · Hi · [K]` |### Cluster I — Collective intelligence / crowds / swarms| Theory | Core claim | For | Against / limits | Coding |
|---|---|---|---|---|
| **Wisdom of Crowds** (Galton 1907 ox-weight; Surowiecki 2004) | Aggregated *independent, diverse* estimates beat most individuals | Robust for estimation tasks | **Fails under correlation/herding/social influence** (Lorenz et al. 2011) | `Active · E3 · Hi · [K]` |
| **Condorcet Jury Theorem** (1785) | Majority of independent >50%-accurate voters → accuracy → 1 as N grows | Mathematical proof | Assumes independence & competence | `Formal · E4(theorem) · Hi · [K]` || **Collective Intelligence factor "c"** (Woolley et al. 2010, Science) | Groups have a general performance factor predicted by *social sensitivity, turn-taking equality, %women* — not avg/max IQ | Original + some replication/extension | Some measurement scrutiny; context limits | `Active · E2 · Md · [K]` |
| **Diversity-trumps-ability** (Hong & Page 2004) | Diverse solver groups can beat high-ability homogeneous ones | Formal + sims | Math contested (Thompson 2014); conditions matter | `Contested · E2 · Md · [K]` || **Swarm intelligence / stigmergy** (Grassé stigmergy; Reynolds 1987 boids; Dorigo ACO; Couzin, Sumpter) | Global order emerges from local rules + indirect (environment-mediated) coordination | Strong models + animal biology | Human applicability partial | `Active · E4(models) · Hi · [K]` |
| **Self-Organized Criticality** (Bak, Tang & Wiesenfeld 1987; neural avalanches — Beggs & Plenz 2003) | Complex systems self-tune to critical points; power-law avalanches; brain may operate near criticality | Sandpile model; some neural data | Universality & "criticality" claims contested | `Active-contested · E2 · Md · [K]` |### Cluster J — Cultural / evolutionary / semiotic / cybernetic| Theory | Core claim | For | Against / limits | Coding |
|---|---|---|---|---|
| **Expression of the Emotions** (Darwin 1872) | Emotional expressions evolved (serviceable habits); cross-species & cross-cultural continuity | Founded modern comparative approach | Read both ways in universality debate | `Foundational · E3 · Hi · [K]` |
| **Emotions as evolved programs** (Tooby & Cosmides; Nesse; Ekman) | Emotions = superordinate programs coordinating sub-systems for recurrent adaptive problems | Coherent adaptationist logic | Just-so-story risk; hard to test specifics | `Active-framework · E3 · Md · [K]` || **Cultural psychology of emotion** (Mesquita; Markus & Kitayama; Tsai "ideal affect") | Culture shapes which emotions matter, display rules, meaning, ideal affect, self-construal | Strong cross-cultural evidence | Within-culture variance large | `Active · E3 · Hi · [K]` |
| **Hyper-/hypocognized emotion; language & emotion** (Levy; Wierzbicka NSM; Lindquist) | Language/culture shape emotional granularity & possibly experience | Ethnographic + lab | "Constitutes vs modulates" open | `Active · E2 · Md · [K]` |
| **Cultural evolution / dual inheritance** (Boyd & Richerson 1985; Henrich 2015) | Norms & affect transmitted by cumulative culture; gene–culture coevolution | Strong theoretical + empirical program | Unit/selection debates | `Active · E3 · Hi · [K]` || **Memetics** (Dawkins 1976; Blackmore 1999) | Culture (incl. affect) spreads as replicating "memes" | Evocative metaphor | **Weak as rigorous science** — no stable replicator unit | `Heuristic · E1 · Md · [K]` |
| **Affect theory (humanities)** (Massumi 2002; Sedgwick via Tomkins) | Affect = pre-personal *intensity* distinct from named emotion | Influential in cultural theory | Contested vs psychology; non-empirical | `Humanities · E0 · Md · [K]` || **Cybernetics / control theory of affect** (Wiener 1948; Ashby homeostasis/requisite variety; Powers Perceptual Control Theory; Sterling *allostasis*) | Emotion/affect = control-theoretic regulation of set-points; feeling ≈ error/feedback signal | Bridges to active inference; allostasis reframes regulation | Abstract; maps loosely to phenomenology | `Active-bridge · E2 · Md · [K]` |
| **Information theory of arousal/aesthetics** (Shannon 1948 → Berlyne 1971 collative variables) | Surprise/entropy/novelty drive arousal & hedonic value (inverted-U) | Aesthetics & curiosity data | Partial | `Active · E2 · Md · [K]` |### Cluster K — Affective computing / Emotion AI| Theory / System | Core claim | For | Against / limits | Coding |
|---|---|---|---|---|
| **Affective Computing** (Picard 1997) | Machines can recognize/express/model emotion; wearable affect sensing | Founded the field; large industry | — | `Field · E3 · Hi · [K]` |
| **Emotion recognition** (face/AU, voice/prosody, text sentiment, physiology EDA/HRV/EEG, multimodal) | Systems infer emotion from signals | Works for coarse valence/engagement *in-domain* | Discrete-emotion inference undercut by Barrett 2019 [V]; **dataset/racial bias** (Rhue: Black players scored "angrier") [V]; poor cross-cultural/individual generalization | `Embattled · E2(coarse)/E1(discrete) · Hi · [V]` || **Computational appraisal agents** (OCC in agents; EMA — Gratch & Marsella 2004; FAtiMA; WASABI) | Rule/appraisal-based synthetic emotion for agents/NPCs/robots | Effective *engineering* for believable agents & HRI | Not a claim about machine feeling | `Active · E3(engineering) · Hi · [K]` |
| **Large-scale sentiment/mood** (VADER; Hedonometer — Dodds & Danforth; "Twitter predicts markets" — Bollen 2011) | Aggregate text reveals population mood / predicts outcomes | Hedonometer tracks large-scale mood | **Market-prediction claims weak/overstated**; lexicon validity limits | `Mixed · E2 · Md · [K]` || **LLM "emotion"** (sentiment neuron — Radford 2017; emotion labeling/generation; support chatbots — Woebot, Replika) | LLMs model & generate affective language, show human-like patterns on some emotion tasks | Behavioral/representational competence real; some clinical support-chatbot benefit | Behavioral ≠ *phenomenal* (hard problem); anthropomorphism & **dependency risks**; support-bot evidence mixed | `Active-contested · E2(behavioral)/E0(phenomenal) · Md · [K]` || **Governance of Emotion AI** (EU AI Act 2024/1689, Art. 5(1)(f)) | Inferring emotions in **workplace/education prohibited** in EU from 2 Feb 2025 (medical/safety exempt); fines ≤ €35M or 7% turnover; not softened by Nov-2025 "omnibus" | In force; enforcement warming (CNIL 2026 priorities) | US has no federal ban (patchwork; Illinois consent rules) | `Active-law · E4(legal fact) · Hi · [V]` |### Cluster L — Behavioral economics / neuroeconomics of affect| Theory | Core claim | For | Against / limits | Coding |
|---|---|---|---|---|
| **Affect heuristic** (Slovic, Finucane et al. 2002) | Feelings serve as information in risk/benefit judgment | Robust; inverse risk-benefit under affect | Boundary conditions | `Active · E3 · Hi · [K]` |
| **Risk-as-feelings** (Loewenstein, Weber, Hsee & Welch 2001) | Emotional reactions to risk diverge from & often override cognitive evaluation | Broad support | — | `Active · E3 · Hi · [K]` |
| **Prospect theory / loss aversion** (Kahneman & Tversky 1979) | Value function is reference-dependent & loss-averse (affective asymmetry) | Prospect theory very robust | Loss-aversion *magnitude/universality* contested (Gal & Rucker 2018) | `Active · E4(PT)/E2(loss-aversion size) · Hi · [K]` || **Appraisal-Tendency Framework** (Lerner et al. 2015 review) | *Specific* emotions produce specific choice biases (fear→pessimism/risk-averse; anger→optimism/risk-seeking); incidental affect carries over | Large integrative evidence base | Context-dependence | `Active · E3 · Hi · [K]` |
| **Neuroeconomics of emotion** (Sanfey et al. 2003 Ultimatum Game; insula/striatum/amygdala) | Emotion is measurable in economic choice (anterior insula & rejection of unfair offers) | fMRI + behavior | Reverse-inference caution | `Active · E3 · Hi · [K]` || **Interoception & risk** (Kandasamy et al. 2016 traders; Werner; Dunn) | Bodily-signal sensitivity ("gut feeling," literally) relates to intuition/risk performance | Heartbeat-detection × outcomes | Small samples; correlational | `Active · E2 · Md · [K]` |### Cross-cluster — Emotion regulation| Theory | Core claim | For | Against / limits | Coding |
|---|---|---|---|---|
| **Process Model of ER** (Gross 1998, 2015) | Regulation via situation selection/modification, attention, cognitive change (*reappraisal*), response modulation (*suppression*); reappraisal generally healthier | Very strong evidence base | Context flexibility matters (no strategy universally "best") | `Active · E4 · Hi · [K]` |
| **Affect labeling** (Lieberman; Torre & Lieberman 2018) | "Name it to tame it" — verbalizing feeling dampens amygdala/distress | Neuroimaging + behavior | Effect sizes modest | `Active · E3 · Hi · [K]` || **Polyvagal theory** (Porges 1994+) | Vagal/autonomic hierarchy governs social-emotional safety states | Popular clinically | **Evolutionary/physiological claims contested** (Grossman & Taylor) | `Popular-contested · E1 · Md · [K]` |---## 3 · Cross-tradition map (Greek · Persian/Islamic · Indian · Chinese · Buddhist · Stoic)

> The user's own domains. These are *serious* prescientific theories of emotion/intuition, several strikingly convergent with modern frameworks. `ANALOG_OF` links to §2 in brackets.| Tradition | Source / thinker | Core concept | Modern analog |
|---|---|---|---|
| **Greek** | Plato (*Republic*) | Tripartite soul: reason / spirit (*thymos*) / appetite | Multi-system control of behavior |
| | Aristotle (*Rhetoric* II, *De Anima*, *Nic. Ethics*) | *Pathē* involve **cognition (appraisal) + bodily change**; *phronesis* = trained perceptual judgment | **Appraisal theory** [A]; expert intuition [F] |
| **Stoic** | Chrysippus, Seneca, Epictetus, Marcus Aurelius | Emotions = **judgments/assent to impressions**; *propatheiai* (pre-emotion first-movements); *apatheia*; *eupatheiai* | **Cognitive appraisal**; explicit ancestor of **CBT** (Ellis/Beck cite Epictetus) [A, +ER] || **Persian/Islamic** | **Ibn Sīnā / Avicenna** (*Kitāb al-Nafs*) | **Wahm** (estimative faculty): perceives non-sensory "intentions" (*maʿānī*) — e.g. sheep sensing wolf's hostility; internal senses; "floating man" self-awareness argument | Medieval theory of **instinct/intuition**; self-consciousness [F, E] |
| | **Al-Ghazālī** (*Iḥyāʾ*) | **Dhawq** ("tasting") = direct experiential/intuitive knowing beyond discursive reason; **qalb** (heart) as organ of knowledge | Intuition as non-discursive knowing; qualia/first-person [E, F] |
| | **Suhrawardī** (Illuminationism / *Ishrāq*) | **Knowledge by presence** (*al-ʿilm al-ḥuḍūrī*) — non-representational, direct self-knowing | Non-representational access; **hard problem/qualia** [E] || | Mullā Ṣadrā | Substantial motion; unity of intellect & intelligible | Process/enactive framing [E] |
| | **Rūmī & Sufism** | **Qalb** (heart-knowledge); ***ʿishq*** (love) as cognitive-affective force; ***ḥāl*** (transient state) vs *maqām* (stable station) | State vs trait affect; affect as epistemic [C, L] |
| **Indian** | Bharata, *Nāṭyaśāstra*; **Abhinavagupta** | **Rasa** theory: 8–9 aestheticized emotions evoked via *bhāvas*; everyday emotion (*bhāva*) vs relished/aesthetic emotion (*rasa*); *śānta* rasa; aesthetic **distance** | Theory of **emotion + empathy + aesthetic regulation** [G, C] |
| | Sāṃkhya/Yoga | *Guṇas*; *citta-vṛtti* (mental fluctuations) modulated by practice | Trait dimensions; emotion regulation [+ER] || **Buddhist** | Abhidhamma; *paṭicca-samuppāda* | **Vedanā** = feeling-tone (pleasant/unpleasant/neutral), 2nd *skandha*; chain: contact→**feeling**→craving; *cetasika* (mental-factor taxonomy); **anattā** (no-self), momentariness | **Core affect/valence** [C]; **constructionism** & contemplative science [C, +ER] |
| **Chinese** | Confucius / **Mencius** | **Four sprouts** (*sìduān*): innate moral feelings — compassion, shame, courtesy, right/wrong | Innate moral emotions / moral intuition [G, F] |
| | Xunzi | Emotions require cultivation via ritual (*lǐ*) | Socialization of affect / display rules [J] |
| | Zhuangzi / Daoism | *Ziran* (spontaneity), *wu-wei*; responding without fixed emotion | Flow; non-deliberative skilled action [F] || | Neo-Confucian | **Xīn = "heart-mind"** (one organ for thinking *and* feeling) | **Affect–cognition integration**; no reason/emotion split [B, C] |
| **Other (breadth stubs)** | Nahua/Aztec (*in ixtli in yollotl* — "face & heart"); Ubuntu (relational personhood); Hebrew (*levav/nefesh*) | Heart as seat of will/emotion; communal/relational affect | Embodied & collective emotion [E, H] |---## 4 · Historical timeline (paradigm shifts)

```
ANCIENT (pre-500 BCE → 500 CE)
  ~1500–500 BCE  Vedic/Upaniṣadic + early Chinese qing (情); Hebrew heart-affect
  ~500–300 BCE   Plato tripartite soul · Aristotle pathē as cognition+body · Mencius four sprouts
  ~300 BCE       Stoics: emotion = judgment; propatheiai · Epicurean ataraxia
  ~200 BCE–200CE Bharata Nāṭyaśāstra (rasa) · Buddhist Abhidhamma (vedanā, no-self)

MEDIEVAL (500–1500)
  ~1000          Avicenna: wahm/estimation = instinct/intuition; internal senses
  ~1100          Al-Ghazālī: dhawq, heart-knowledge
  ~1190          Suhrawardī: knowledge by presence
  ~1000–1300     Abhinavagupta (rasa-realization) · Rūmī (ʿishq, qalb)EARLY MODERN (1500–1850)
  1649  Descartes  — Passions of the Soul (6 primitives, pineal gland)
  1677  Spinoza    — affectus & conatus (proto-appraisal + homeostasis)
  1739  Hume       — passions primary; sympathy (proto-contagion/empathy)
  1759  A. Smith   — moral sentiments; impartial spectator (proto-empathy)

FOUNDING OF SCIENTIFIC STUDY (1850–1930)
  1872  Darwin     — Expression of the Emotions (evolutionary, cross-species)
  1884/85 James/Lange — bodily-feedback theory of emotion
  1890s Wundt/James — experimental psychology; introspection
  1895  Le Bon     — crowd psychology (collective "mind")
  1907  Galton     — vox populi (wisdom of crowds)
  1912  Durkheim   — collective effervescence
  1927/28 Cannon/Bard — thalamic theory; critique of JamesMID-20th CENTURY: circuits, cognition, culture (1930–1980)
  1937  Papez · 1949 MacLean limbic/triune (later discredited)
  1948  Shannon (information) · Wiener (cybernetics) · Ashby homeostasis
  1960–66 Arnold/Lazarus — appraisal theory
  1962  Schachter–Singer two-factor · Tomkins affect programs
  1971/78 Ekman universality thesis + FACS
  1972  Kahneman & Tversky — heuristics & biases begin
  1974  Nagel "What is it like to be a bat?"COGNITIVE + AFFECTIVE REVOLUTION (1980–2000)
  1980  Zajonc (affect primacy) vs Lazarus debate · Russell circumplex · Plutchik
  1985  Boyd & Richerson (cultural evolution)
  1988  Baars Global Workspace · OCC appraisal model · PANAS
  1991  Varela/Thompson/Rosch — The Embodied Mind (enactivism)
  1992  Mirror neurons discovered (di Pellegrino/Rizzolatti)
  1994  Damasio — Descartes' Error (somatic markers)
  1995  Chalmers — the "hard problem"
  1996  LeDoux — The Emotional Brain · Gigerenzer fast-and-frugal · dopamine RPE (1997)
  1997  Picard — Affective Computing · Schachter-Singer legacy
  1998  Panksepp — Affective Neuroscience · Gross process model of ER · Fredrickson broaden-build21st CENTURY: prediction, construction, networks, replication crisis (2000–2020)
  2001  Loewenstein risk-as-feelings · 2002 Slovic affect heuristic; Preston–de Waal
  2003  Sanfey neuroeconomics (Ultimatum Game) · Beggs–Plenz neural avalanches
  2004  Tononi IIT (v1) · Surowiecki Wisdom of Crowds · Collins interaction ritual chains
  2006  Barrett conceptual-act (→ constructed emotion) · Friston free-energy · Dijksterhuis UTT
  2007  Christakis–Fowler obesity/2008 happiness contagion · Centola–Macy complex contagion
  2010  Woolley collective-intelligence factor · Cuddy power-pose (2010→later disavowed)
  2011  Shalizi–Thomas (homophily confound) · Kahneman Thinking Fast & Slow
  2012  Bond 61M-person voting-contagion experiment · Cambridge Declaration on Consciousness
  2013  Seth interoceptive inference · Graziano attention schema
  2015  ***Replication crisis crests***: power-pose (Ranehill), ego depletion, priming; Kahneman–Klein synthesis
  2016  Facial-feedback (Strack) fails to replicate · Eldar mood-as-momentum
  2017  Barrett How Emotions Are Made · Cowen–Keltner 27 emotions · Brady moral contagion · OpenAI sentiment neuronRECENT (2020 → now)  [several items verified this session, [V]]
  2019  Barrett et al. — Emotional Expressions Reconsidered (undercuts face→emotion) [V]
  2023  IIT branded "pseudoscience" by 124-signatory open letter [V] · COGITATE GNWT-vs-IIT adversarial results
  2024  EU AI Act in force (1 Aug); NY Declaration on Animal Consciousness
  2025  EU AI Act Art. 5(1)(f) — workplace/education emotion-inference PROHIBITED (2 Feb) [V]
  2026  EU "Digital Omnibus" leaves emotion-AI prohibition intact; enforcement ramps [V]
  now   Open: hard problem unsolved; LLM-affect debate; unifying predictive accounts
```**Current (contested) consensus tendencies** — stated as *tendencies*, not settled fact:
- Emotion ↔ cognition are **integrated**, not separate faculties (broad agreement).
- **No consistent 1-to-1 biomarker/facial "fingerprint"** for discrete emotion categories has been found (strong result [V]; interpretation still fought over).
- **Interoception & prediction** are central to feeling (rising consensus).
- **Reappraisal-type regulation** works; specific strategies are context-dependent.
- **Consciousness/qualia** remain genuinely unexplained (the hard problem is live).

---## 5 · Contradictions & live debates matrix| # | Debate | Camp X | Camp Y | Status |
|---|---|---|---|---|
| D1 | Nature of emotion | **Basic/discrete natural kinds** (Ekman, Panksepp, Keltner) | **Constructed categories** (Barrett) | Unresolved; empirically active; [V] evidence pressures strong-fingerprint claims |
| D2 | Cognition vs affect primacy | **Appraisal first** (Lazarus) | **Affect first** (Zajonc) | Largely *reconciled*: dual routes (LeDoux) |
| D3 | Localization | **Dedicated circuits** (LeDoux-early, Panksepp) | **Distributed/constructionist** (Pessoa, Barrett) | Converging on "hubs + distributed," details fought |
| D4 | What is a feeling? | **Perception of body** (James, Damasio, Seth) | **Central/cognitive constitution** | Open; interoception evidence favors X-ish || D5 | Network affect contagion | **Real 3-degree spread** (Christakis–Fowler) | **Confounded by homophily/environment** (Shalizi, Fletcher, Lyons) | Skeptics have upper hand for *happiness/loneliness* [V] |
| D6 | Consciousness theory | **GNWT** (Dehaene) | **IIT** (Tononi) | Adversarial (COGITATE); IIT also charged as pseudoscience [V] |
| D7 | Heuristics | **Biases/flaws** (Kahneman) | **Ecologically rational** (Gigerenzer) | Both partly right; context-dependent |
| D8 | Unconscious-thought advantage | **Exists** (Dijksterhuis) | **Fails to replicate** (Nieuwenstein) | Skeptics winning |
| D9 | Dual-process architecture | **Two systems** | **Continuum / "mythical number two"** (Melnikoff & Bargh) | Trending toward continuum || D10 | Facial feedback | **Robust** (Strack) | **Small/none** (many-labs 2016) | Small effect likely (Coles meta) |
| D11 | Emotion without language | **Yes — prelinguistic/animal affect** | **Concepts/language required for discrete emotion** (constructionism) | Core affect yes; categories contested |
| D12 | Mirror neurons | **Basis of empathy/understanding** | **Overhyped** (Hickok, Heyes) | Existence yes; grand claims deflated |
| D13 | Machine emotion | **LLMs/agents can have functional affect** | **Behavioral only; no phenomenal feeling** | Behavioral yes; phenomenal = hard problem |---## 6 · Cross-cutting questions → current-state answers

> Each: short verdict · key evidence · confidence · open edge. Verdicts are *state-of-field summaries*, not endorsements.1. **Can emotion be quantified?** — *Partially.* Dimensional (valence/arousal) + physiological/behavioral proxies quantify *aspects*; discrete-category inference is **unreliable** [V]. No ground-truth "emotion-meter"; measurement is construct-dependent. `C-Hi`. Open: idiographic, real-time, ground-truthed measurement.
2. **Can intuition be predicted?** — *Its accuracy, yes; its content, less so.* Trustworthy iff environment is regular + high-feedback (Kahneman–Klein 2009); much "intuition" = predictable implicit statistical learning. `C-Hi`.
3. **Can collective emotions emerge from simple interactions?** — *Plausibly yes in models*; strong macro claims (network happiness) contested by confounding [V]. Mechanism plausible, magnitude uncertain. `C-Md`.4. **How do emotions spread through networks?** — Mimicry + afferent feedback (Hatfield); social appraisal (EASI); moral-emotional amplification (Brady/Crockett); **complex contagion** needs reinforcement (Centola). Online textual contagion small-but-real [V]; behavior contagion real (Bond). Confounds: homophily, shared exposure. `C-Md`.
5. **Can emotional synchronization be measured?** — *Yes* (physiological synchrony, hyperscanning, behavioral entrainment) but **artifact-prone** (shared stimulus ≠ coupling); causality open. `C-Md`.6. **Are there universal emotional patterns?** — Some regularities (valence/arousal; above-chance recognition; partial autonomic patterns), but **universal discrete facial fingerprints not supported** [V]; Keltner/Cowen defend a broader universal repertoire. Contested. `C-Md`.
7. **How does culture modify emotion?** — Display rules, concepts/granularity (hyper/hypocognition), ideal affect (Tsai), self-construal (Markus–Kitayama), situational meaning (Mesquita). Strong evidence for shaping expression, regulation, salience, possibly experience. `C-Hi`.8. **How do hormones affect emotion?** — Cortisol (stress), testosterone (dominance), dopamine (reward/RPE), serotonin (mood/aggression), oxytocin (affiliation — **overhyped**, replication issues). Hormones *bias thresholds/tendencies*, don't determine specific feelings. `C-Md`.
9. **How does memory interact with feeling?** — Mood-congruent memory & mood-dependent recall; amygdala–hippocampus emotional enhancement (flashbulb memories — vivid but *accuracy overestimated*); **reconsolidation** (Nader/LeDoux) enables updating emotional memories (clinical use); constructed emotion draws on stored concepts. `C-Hi`.10. **How does uncertainty affect intuition?** — Uncertainty ↑ reliance on affect/heuristics; anxiety → pessimism/narrowing; predictive-processing: unresolved prediction error ≈ arousal/negative affect; ambiguity aversion (insula). `C-Md`.
11. **How does prediction influence emotion?** — Core to predictive/interoceptive accounts: emotions as *predictions* about (internal) states; prediction error & its *rate of change* → affect (mood-as-momentum, Eldar); expected value → valence. `C-Md`.
12. **Can emotion exist without language?** — *Core affect: yes* (prelinguistic infants, animals). *Discrete named emotions:* constructionists argue language/concepts shape/constitute them. Exactly how much: contested. `C-Md`.13. **How do animals experience emotion?** — Strong evidence for **valenced affective states** (Panksepp primary emotions; rat 50-kHz play calls; **judgment/cognitive-bias tests** as welfare measures — Harding, Paul & Mendl 2004). Phenomenology inferential (Cambridge Declaration 2012; NY Declaration 2024). Feeling likely; rich human-like discrete emotions uncertain. `C-Md`.
14. **Can machines simulate emotion?** — *Simulate/express/represent:* yes (appraisal agents, LLMs, robots) and they causally move human affect. *Have/feel:* no evidence, and category-inference is unreliable + now EU-prohibited in workplace/education [V]. Behavioral simulation ≠ phenomenal experience (hard problem). `C-Hi`.---## 7 · Knowledge graph (curated edge list)

> Representative core edges using the §0 vocabulary. Extend via the schema in §8. `A --REL--> B`.

```
# Emotion theory lineage
JamesLange        --GROUNDS-->        SomaticMarker
SomaticMarker     --EXTENDS-->        JamesLange
CannonBard        --CONTRADICTS-->    JamesLange
SchachterSinger   --EXTENDS-->        JamesLange           # adds cognitive label
Appraisal         --COMPETES_WITH-->  AffectPrimacy
ConstructedEmotion--CONTRADICTS-->    BasicEmotion
ConstructedEmotion--GROUNDED_IN-->    PredictiveProcessing
ComponentProcess  --SPECIAL_CASE_OF-->Appraisal
FacialFeedback    --SUPPORTS-->       JamesLange           # (weakly; see D10)# Predictive / computational
ActiveInference   --EXTENDS-->        BayesianBrain
FreeEnergyPrinciple--SUBSUMES-->      ActiveInference
InteroceptiveInference--SPECIAL_CASE_OF-->ActiveInference
EPIC              --SUPPORTS-->       ConstructedEmotion
DopamineRPE       --GROUNDS-->        MoodAsMomentum
MoodAsMomentum    --OPERATIONALIZES-->CoreAffect

# Measurement
Circumplex        --OPERATIONALIZES-->CoreAffect
PANAS             --MEASURES-->       PositiveNegativeAffect
FACS              --MEASURES-->       FacialActionUnits
PCI               --MEASURES-->       IIT_phi                # perturbational complexity
EmotionRecognitionAI--APPLIES-->      FACS
EmotionRecognitionAI--CONTESTED_BY--> Barrett2019# Consciousness
GNWT              --COMPETES_WITH-->  IIT
PseudoscienceLetter2023--CONTESTED_BY-->IIT
Enactivism        --CONTRADICTS-->    Representationalism
AttentionSchema   --EXTENDS-->        HigherOrderTheory

# Intuition
DualProcess       --SUBSUMES-->       HeuristicsAndBiases
Gigerenzer        --COMPETES_WITH-->  Kahneman
RecognitionPrimedDecision--SPECIAL_CASE_OF-->ImplicitLearning
UnconsciousThought--CONTESTED_BY-->   Nieuwenstein2015
KahnemanKlein2009 --SUBSUMES-->       RecognitionPrimedDecision

# Empathy
MirrorNeurons     --PROPOSED_BASIS_FOR-->Empathy
Hickok            --CONTESTED_BY-->   MirrorNeurons          # deflates empathy claim
PerceptionActionModel--GROUNDS-->     EmotionalContagion
EmotionalContagion--GROUNDS-->        CollectiveEmotion# Collective / networks
ComplexContagion  --CONTRADICTS-->    SimpleDiseaseContagion
ChristakisFowler  --CONTESTED_BY-->   HomophilyConfound
Durkheim          --PRECEDES-->       InteractionRitualChains
LeBon             --CONTESTED_BY-->    ElaboratedSocialIdentityModel
GroupAffect       --SPECIAL_CASE_OF-->EASI

# Collective intelligence
WisdomOfCrowds    --SPECIAL_CASE_OF-->CondorcetJuryTheorem
WoolleyC          --EXTENDS-->        WisdomOfCrowds          # to problem-solving
SwarmIntelligence --GROUNDS-->        CollectiveIntelligence
SelfOrganizedCriticality--GROUNDS-->  NeuralAvalanches

# Cultural / cybernetic / info
Allostasis        --EXTENDS-->        Homeostasis
Cybernetics       --GROUNDS-->        ControlTheoryOfAffect
Shannon           --GROUNDS-->        BerlyneArousal# Applied / governance
AffectiveComputing--APPLIES-->        Appraisal
AffectiveComputing--APPLIES-->        DimensionalModels
EmotionAI         --REGULATED_BY-->   EU_AIAct_Art5_1f

# Cross-tradition analogs
AvicennaWahm      --ANALOG_OF-->      Instinct_Intuition
StoicAppraisal    --PRECEDES-->       CBT_Appraisal
Rasa              --ANALOG_OF-->      AestheticEmpathy
Vedana            --ANALOG_OF-->      CoreAffect_Valence
XinHeartMind      --ANALOG_OF-->      AffectCognitionIntegration
SpinozaAffectus   --ANALOG_OF-->      Conatus_Homeostasis
```

---## 8 · Ingestion schema (JSON) — for building the actual DB

> Drop-in schema to grow this beyond v1. Designed for a graph DB or Obsidian+Dataview / GraphRAG.```json
{
  "TheoryNode": {
    "id": "string (slug, unique)",
    "name": "string",
    "authors": ["string"],
    "year": "integer | [start, end]",
    "cluster": "A|B|C|D|E|F|G|H|I|J|K|L|ER|TRADITION",
    "field": ["string"],
    "core_hypothesis": "string",
    "variables": { "inputs": ["string"], "outputs": ["string"], "latent": ["string"] },
    "computational_model": "string | null",
    "math_formalism": "string | null",
    "hidden_assumptions": ["string"],
    "predictions": ["string"],
    "evidence_for": [{ "claim": "string", "citation": "string", "strength": "E0-E4" }],
    "evidence_against": [{ "claim": "string", "citation": "string" }],
    "key_experiments": [{ "name": "string", "result": "string", "n": "integer|null" }],
    "replication_status": "replicated|mixed|failed|untested|na",
    "known_failures": ["string"],
    "limitations": ["string"],
    "open_questions": ["string"],
    "status": "Active|Foundational|Contested|Discredited",
    "evidence_level": "E0|E1|E2|E3|E4",
    "confidence": "Hi|Md|Lo",
    "provenance": "V|K|V/K",
    "tags": ["string"]
  },
  "Edge": {
    "from": "TheoryNode.id",
    "to": "TheoryNode.id",
    "relation": "SUPPORTS|CONTRADICTS|EXTENDS|SUBSUMES|SPECIAL_CASE_OF|OPERATIONALIZES|MEASURES|GROUNDS|GROUNDED_IN|COMPETES_WITH|PRECEDES|CONTESTED_BY|PROPOSED_BASIS_FOR|APPLIES|REGULATED_BY|ANALOG_OF",
    "weight": "float 0-1 (strength/confidence of relation)",
    "note": "string"
  },
  "Debate": {
    "id": "Dn",
    "question": "string",
    "camp_x": { "label": "string", "proponents": ["string"] },
    "camp_y": { "label": "string", "proponents": ["string"] },
    "status": "open|leaning_x|leaning_y|reconciled",
    "linked_nodes": ["TheoryNode.id"]
  },
  "TraditionNode": {
    "id": "string",
    "tradition": "Greek|Persian-Islamic|Indian|Chinese|Buddhist|Stoic|Other",
    "thinker": "string",
    "source_text": "string",
    "concept_native": "string (transliterated)",
    "gloss": "string",
    "modern_analog": ["TheoryNode.id"]
  }
}
```---## 9 · Consolidated research gaps1. **Ground-truth problem** — no objective referent for "the emotion someone is in"; all measures are proxies.
2. **Discrete-emotion biomarker** — no reliable neural/physiological/facial signature per category [V].
3. **Hard problem** — no accepted bridge between measurable correlates and phenomenal experience.
4. **Causal (not correlational) inter-brain synchrony** — disentangle true coupling from shared-stimulus artifact.
5. **Contagion vs homophily vs shared environment** at population scale [V].
6. **WEIRD sampling bias** — most emotion data from Western, educated samples; cross-cultural coverage thin.
7. **Animal phenomenology criteria** — behavioral/affective evidence strong; consciousness inference unresolved.8. **LLM/agent "affect"** — whether functional analogues exist, and how to test them without anthropomorphizing.
9. **Falsifiability of grand unifying theories** (FEP/active inference; IIT) — making them risky and testable.
10. **Idiographic vs nomothetic dynamics** — person-specific emotion trajectories vs group averages.
11. **Ecological, real-time measurement** — most data is lab-bound; naturalistic capture needed.
12. **Neuroimmune/inflammatory contributions** (e.g., inflammation–depression link) integrated with affect models.
13. **Developmental origin of emotion concepts** — how/when constructionist "concepts" form.
14. **Reproducibility of embodiment/priming/facial-feedback effects** — sizes and moderators.
15. **Governance & ethics of Emotion AI** — deploying tools whose scientific validity is contested [V].---## 10 · Provenance & caveats- **Verified this session `[V]`** (web-checked 2026-07): Facebook emotional-contagion study details & tiny effect; Christakis–Fowler happiness-contagion + homophily-confound critiques; power-pose replication failure & Carney's disavowal; IIT 2023 "pseudoscience" letter (124 signatories); Barrett et al. 2019 face→emotion critique; EU AI Act Art. 5(1)(f) emotion-recognition prohibition (in force 2 Feb 2025; not softened Nov 2025); emotion-AI dataset bias (Rhue).
- **Knowledge-based `[K]`** rows are expert summaries not re-verified this pass — reliable for orientation, but **spot-check specific years/effect sizes before publishing or citing**, especially older lab studies subject to the replication crisis.- This v1 **compresses** entire sub-literatures into single rows. Any row can be expanded into a full `TheoryNode` (§8).
- Nothing here forces a conclusion on the two central fault lines (natural-kind vs constructed emotion; feeling as body-perception vs central). Both are preserved as live.---### Suggested extension order (if you build this out)
`Cluster C (discrete vs constructed)` → `Cluster D (predictive/active inference)` → `Cluster H (contagion/synchrony)` are the highest-leverage branches for a computational/complex-systems framework, and they interlock (predictive processing grounds constructionism; contagion/synchrony are the collective-scale expression of the same dynamics).