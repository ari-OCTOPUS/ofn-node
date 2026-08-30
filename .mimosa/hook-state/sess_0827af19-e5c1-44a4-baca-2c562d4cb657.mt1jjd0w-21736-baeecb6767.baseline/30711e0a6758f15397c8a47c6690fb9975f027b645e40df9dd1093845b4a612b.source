const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  PageBreak, Header, Footer, PageNumber, AlignmentType, HeadingLevel,
  WidthType, BorderStyle, ShadingType, SectionType, TableLayoutType,
  TableOfContents, LevelFormat,
} = require("docx");
const fs = require("fs");

// ─── PALETTE: DM-1 (Deep Cyan) for AI/Tech report ───
const coverPalettes = {
  "DM-1": {
    bg: "162235", primary: "FFFFFF", accent: "37DCF2",
    cover: { titleColor: "FFFFFF", subtitleColor: "B0B8C0", metaColor: "90989F", footerColor: "687078" },
    table: { headerBg: "1B6B7A", headerText: "FFFFFF", accentLine: "1B6B7A", innerLine: "C8DDE2", surface: "EDF3F5" },
  },
};
const P = coverPalettes["DM-1"];
const T = P.table;
const c = (hex) => hex.replace("#", "");

// ─── BORDERS ───
const NB = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: NB, bottom: NB, left: NB, right: NB };
const allNoBorders = { top: NB, bottom: NB, left: NB, right: NB, insideHorizontal: NB, insideVertical: NB };

// ─── COVER HELPERS ───
function calcTitleLayout(title, maxWidthTwips, preferredPt = 40, minPt = 24) {
  const charWidth = (pt) => pt * 20;
  const charsPerLine = (pt) => Math.floor(maxWidthTwips / charWidth(pt));
  let titlePt = preferredPt;
  let lines;
  while (titlePt >= minPt) {
    const cpl = charsPerLine(titlePt);
    if (cpl < 2) { titlePt -= 2; continue; }
    lines = splitTitleLines(title, cpl);
    if (lines.length <= 3) break;
    titlePt -= 2;
  }
  if (!lines || lines.length > 3) {
    const cpl = charsPerLine(minPt);
    lines = splitTitleLines(title, cpl);
    titlePt = minPt;
  }
  return { titlePt, titleLines: lines };
}

function splitTitleLines(title, charsPerLine) {
  if (title.length <= charsPerLine) return [title];
  const breakAfter = new Set([...' ,;:!', ...'-_/ \t']);
  const lines = [];
  let remaining = title;
  while (remaining.length > charsPerLine) {
    let breakAt = -1;
    for (let i = charsPerLine; i >= Math.floor(charsPerLine * 0.6); i--) {
      if (i < remaining.length && breakAfter.has(remaining[i - 1])) { breakAt = i; break; }
    }
    if (breakAt === -1) {
      const limit = Math.min(remaining.length, Math.ceil(charsPerLine * 1.3));
      for (let i = charsPerLine + 1; i < limit; i++) {
        if (breakAfter.has(remaining[i - 1])) { breakAt = i; break; }
      }
    }
    if (breakAt === -1) breakAt = charsPerLine;
    lines.push(remaining.slice(0, breakAt).trim());
    remaining = remaining.slice(breakAt).trim();
  }
  if (remaining) lines.push(remaining);
  if (lines.length > 1 && lines[lines.length - 1].length <= 2) {
    const last = lines.pop();
    lines[lines.length - 1] += last;
  }
  return lines;
}

function calcCoverSpacing(params) {
  const {
    titleLineCount = 1, titlePt = 36, hasSubtitle = false,
    hasEnglishLabel = false, metaLineCount = 0,
    fixedHeight = 800, pageHeight = 16838,
    marginTop = 0, marginBottom = 0,
  } = params;
  const SAFETY = 1200;
  const usableHeight = pageHeight - marginTop - marginBottom - SAFETY;
  const titleHeight = titleLineCount * (titlePt * 23 + 200);
  const subtitleHeight = hasSubtitle ? (12 * 23 + 600) : 0;
  const englishLabelHeight = hasEnglishLabel ? (9 * 23 + 600) : 0;
  const metaHeight = metaLineCount * (10 * 23 + 100);
  const implicitParaHeight = 3 * 300;
  const contentHeight = titleHeight + subtitleHeight + englishLabelHeight + metaHeight + fixedHeight + implicitParaHeight;
  const remainingSpace = usableHeight - contentHeight;
  const safeRemaining = Math.max(remainingSpace, 400);
  const FOOTER_MIN = 800;
  const rawTop = Math.floor(safeRemaining * 0.45);
  const rawBottom = Math.floor(safeRemaining * 0.45);
  const bottomSpacing = Math.max(rawBottom, FOOTER_MIN);
  const topSpacing = Math.max(rawTop - Math.max(0, FOOTER_MIN - rawBottom), 400);
  const midSpacing = Math.max(safeRemaining - topSpacing - bottomSpacing, 0);
  return { topSpacing, midSpacing, bottomSpacing };
}

// ─── COVER R1: Pure Paragraph Left with DM-1 ───
function buildCoverR1(config) {
  const PC = P.cover;
  const padL = 1200, padR = 800;
  const availableWidth = 11906 - padL - padR - 300;
  const { titlePt, titleLines } = calcTitleLayout(config.title, availableWidth, 40, 24);
  const titleSize = titlePt * 2;
  const spacing = calcCoverSpacing({
    titleLineCount: titleLines.length, titlePt,
    hasSubtitle: !!config.subtitle, hasEnglishLabel: !!config.englishLabel,
    metaLineCount: (config.metaLines || []).length,
    fixedHeight: 400,
  });
  const accentLeft = { style: BorderStyle.SINGLE, size: 8, color: P.accent, space: 12 };
  const children = [];

  children.push(new Paragraph({ spacing: { before: spacing.topSpacing } }));

  if (config.englishLabel) {
    children.push(new Paragraph({
      indent: { left: padL, right: padR }, spacing: { after: 500 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: P.accent, space: 8 } },
      children: [new TextRun({ text: config.englishLabel, size: 18, color: P.accent,
        font: { ascii: "Calibri", eastAsia: "SimHei" }, characterSpacing: 40 })],
    }));
  }

  for (let i = 0; i < titleLines.length; i++) {
    children.push(new Paragraph({
      indent: { left: padL },
      spacing: { after: i < titleLines.length - 1 ? 100 : 300, line: Math.ceil(titlePt * 23), lineRule: "atLeast" },
      children: [new TextRun({ text: titleLines[i], size: titleSize, bold: true,
        color: PC.titleColor, font: { eastAsia: "SimHei", ascii: "Arial" } })],
    }));
  }

  if (config.subtitle) {
    children.push(new Paragraph({
      indent: { left: padL }, spacing: { after: 800 },
      children: [new TextRun({ text: config.subtitle, size: 24, color: PC.subtitleColor,
        font: { eastAsia: "Microsoft YaHei", ascii: "Arial" } })],
    }));
  }

  for (const line of (config.metaLines || [])) {
    children.push(new Paragraph({
      indent: { left: padL + 200 }, spacing: { after: 80 },
      border: { left: accentLeft },
      children: [new TextRun({ text: line, size: 24, color: PC.metaColor,
        font: { eastAsia: "Microsoft YaHei", ascii: "Arial" } })],
    }));
  }

  children.push(new Paragraph({ spacing: { before: spacing.bottomSpacing } }));

  children.push(new Paragraph({
    indent: { left: padL, right: padR },
    border: { top: { style: BorderStyle.SINGLE, size: 2, color: P.accent, space: 8 } },
    spacing: { before: 200 },
    children: [
      new TextRun({ text: config.footerLeft || "", size: 16, color: PC.footerColor, font: { ascii: "Arial" } }),
      new TextRun({ text: "                                        " }),
      new TextRun({ text: config.footerRight || "", size: 16, color: PC.footerColor, font: { ascii: "Arial" } }),
    ],
  }));

  return [new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    borders: allNoBorders,
    rows: [new TableRow({
      height: { value: 16838, rule: "exact" },
      children: [new TableCell({
        shading: { type: ShadingType.CLEAR, fill: P.bg }, borders: noBorders,
        children,
      })],
    })],
  })];
}

// ─── SAFE TEXT HELPER ───
function safeText(value, placeholder) {
  if (value === undefined || value === null || value === "" || String(value) === "NaN") {
    return placeholder || "[To be filled]";
  }
  return String(value);
}

// ─── TABLE HELPERS ───
function makeHeaderCell(text, widthPct) {
  return new TableCell({
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: safeText(text), bold: true, size: 20, color: T.headerText,
        font: { ascii: "Times New Roman", eastAsia: "SimHei" } })],
    })],
    shading: { type: ShadingType.CLEAR, fill: T.headerBg },
    borders: noBorders,
    margins: { top: 60, bottom: 60, left: 120, right: 120 },
    width: { size: widthPct, type: WidthType.PERCENTAGE },
  });
}

function makeDataCell(text, widthPct, rowIndex) {
  return new TableCell({
    children: [new Paragraph({
      spacing: { line: 276 },
      children: [new TextRun({ text: safeText(text), size: 20, color: "000000",
        font: { ascii: "Times New Roman", eastAsia: "SimSun" } })],
    })],
    shading: rowIndex % 2 === 0 ? { type: ShadingType.CLEAR, fill: T.surface } : { type: ShadingType.CLEAR, fill: "FFFFFF" },
    borders: noBorders,
    margins: { top: 60, bottom: 60, left: 120, right: 120 },
    width: { size: widthPct, type: WidthType.PERCENTAGE },
  });
}

function makeTable(headers, rows, colWidths) {
  const headerRow = new TableRow({
    tableHeader: true, cantSplit: true,
    children: headers.map((h, i) => makeHeaderCell(h, colWidths[i])),
  });
  const dataRows = rows.map((row, ri) =>
    new TableRow({
      cantSplit: true,
      children: row.map((cell, ci) => makeDataCell(cell, colWidths[ci], ri)),
    })
  );
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    borders: {
      top: { style: BorderStyle.SINGLE, size: 2, color: T.accentLine },
      bottom: { style: BorderStyle.SINGLE, size: 2, color: T.accentLine },
      left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 1, color: T.innerLine },
      insideVertical: { style: BorderStyle.NONE },
    },
    rows: [headerRow, ...dataRows],
  });
}

// ─── BODY HELPERS ───
function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    alignment: AlignmentType.CENTER,
    spacing: { before: 480, after: 200, line: 312 },
    children: [new TextRun({ text: safeText(text), bold: true, size: 32, color: "0A1628",
      font: { ascii: "Times New Roman", eastAsia: "SimHei" } })],
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 360, after: 160, line: 312 },
    children: [new TextRun({ text: safeText(text), bold: true, size: 28, color: "0A1628",
      font: { ascii: "Times New Roman", eastAsia: "SimHei" } })],
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 240, after: 120, line: 312 },
    children: [new TextRun({ text: safeText(text), bold: true, size: 24, color: "0A1628",
      font: { ascii: "Times New Roman", eastAsia: "SimHei" } })],
  });
}

function body(text) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    indent: { firstLine: 480 },
    spacing: { after: 120, line: 312 },
    children: [new TextRun({ text: safeText(text), size: 24, color: "000000",
      font: { ascii: "Times New Roman", eastAsia: "SimSun" } })],
  });
}

function bodyNoIndent(text) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 120, line: 312 },
    children: [new TextRun({ text: safeText(text), size: 24, color: "000000",
      font: { ascii: "Times New Roman", eastAsia: "SimSun" } })],
  });
}

function tableTitle(text) {
  return new Paragraph({
    keepNext: true,
    spacing: { before: 200, after: 100 },
    children: [new TextRun({ text: safeText(text), bold: true, size: 21, color: "0A1628",
      font: { ascii: "Times New Roman", eastAsia: "SimHei" } })],
  });
}

// ─── REPORT CONTENT ───

const coverConfig = {
  title: "AGI Infrastructure Investment Report",
  subtitle: "How Companies Are Investing in Artificial General Intelligence Through Infrastructure, Compute, and Physical Assets",
  englishLabel: "COMPREHENSIVE MARKET ANALYSIS  |  AUGUST 2026",
  metaLines: [
    "Technology Sector Research",
    "Infrastructure, Compute & Physical Assets",
    "Global Coverage: North America, Asia-Pacific, Europe",
  ],
  footerLeft: "Confidential Research Report",
  footerRight: "August 2026",
  palette: P,
};

const executiveSummary = [
  body("The race toward Artificial General Intelligence (AGI) has triggered an unprecedented wave of infrastructure investment across the global technology sector. As of August 2026, the world's largest technology companies, alongside a constellation of well-funded startups, are deploying hundreds of billions of dollars annually into custom silicon, hyperscale data centers, nuclear energy agreements, advanced networking, training data acquisition, and cloud AI platforms. This report provides a comprehensive mapping of these investments across six critical areas, detailing specific company commitments, dollar amounts, timelines, and strategic rationales."),
  body("The scale of investment is staggering. The combined 2026 capital expenditure of the top five technology companies -- Microsoft, Amazon, Google, Meta, and Apple -- is projected to exceed $600 billion, with a substantial and growing share directed specifically toward AI infrastructure. Nvidia alone recorded $216 billion in fiscal year 2026 revenue, with its AI accelerator chips commanding approximately 80% of the market for enterprise AI training and inference. The Stargate project, a joint venture backed by OpenAI, SoftBank, Oracle, and others, has committed $500 billion over multiple phases to construct what will be the world's largest AI computing complex in Abilene, Texas, targeting 10 gigawatts of power capacity."),
  body("Beyond hardware, the investment landscape extends into nuclear energy procurement -- with Microsoft, Amazon, and Google all signing multi-decade power purchase agreements totaling tens of gigawatts -- advanced networking infrastructure including trans-oceanic submarine cables valued at over $10 billion, and an increasingly contested market for training data where licensing deals range from $5 million to $250 million per agreement. The cloud AI platform market, led by AWS Bedrock, Google Vertex AI (rebranded as the Gemini Enterprise Agent Platform), and Azure AI Foundry, has become the primary distribution channel for AGI capabilities, with Google Cloud alone reaching $24.8 billion in Q2 2026 revenue, an 82% year-over-year increase."),
  body("This report examines each of these six investment domains in depth, providing investors, policymakers, and technology leaders with a detailed atlas of where capital is flowing, what is being built, and why these investments matter for the trajectory toward AGI."),
];

const section1_chips = [
  h1("1. Custom Silicon and AI Chips"),
  body("Custom silicon represents the foundational layer of AGI infrastructure. The companies investing most heavily in AGI have uniformly concluded that general-purpose processors cannot deliver the compute density, energy efficiency, or cost structure required for frontier AI workloads at scale. This has triggered a proliferation of custom ASIC (Application-Specific Integrated Circuit) designs, each tailored to the specific computational patterns of large language model training and inference."),

  h2("1.1 Nvidia: Blackwell, Rubin, and Market Dominance"),
  body("Nvidia remains the undisputed leader in AI accelerator silicon. In fiscal year 2026 (ending January 2026), the company recorded $216 billion in total revenue, with its data center segment -- driven overwhelmingly by AI GPU sales -- accounting for the vast majority. The company maintains approximately 80% market share for enterprise AI training chips and an even higher share for inference accelerators used in production AI deployments."),
  body("The Nvidia Hopper (H100/H200) architecture, launched in 2022-2023, established the standard for AI training performance. In 2024, the company began volume production of its Blackwell architecture (B200 and GB200 Grace-Blackwell superchips), which delivers approximately 4x the inference performance and 2x the training throughput of Hopper for transformer workloads. Blackwell features 208 billion transistors on a 4nm TSMC process, with second-generation Transformer Engine technology and fifth-generation NVLink interconnect providing 1.8 TB/s of bi-directional bandwidth."),
  body("Looking forward, Nvidia has announced the Rubin architecture, expected to reach volume production in late 2026 or early 2027. Rubin will utilize TSMC's 3nm process node and feature next-generation NVLink with even higher bandwidth, alongside improvements in sparse computation and FP4 precision support. The company's networking division, which includes InfiniBand and Ethernet switching products, generated $7.3 billion in revenue in FY2026, underscoring that Nvidia's silicon strategy extends well beyond GPUs into full-stack AI infrastructure."),

  h2("1.2 Google: TPU v6, Ironwood, and the Broadcom Partnership"),
  body("Google has been designing custom AI accelerators since 2015, making its Tensor Processing Unit (TPU) program one of the longest-running in the industry. The current generation, TPU v5p, powers Google's internal AI workloads and is available to cloud customers via Google Cloud. In 2026, Google is deploying its next-generation TPU, code-named Ironwood (v7x), which represents a significant architectural leap in performance-per-watt."),
  body("Google's most significant silicon investment, however, is its partnership with Broadcom. In June 2025, Google signed a multi-year agreement valued at approximately $46 billion with Broadcom to co-design and manufacture custom AI ASICs. This deal represents one of the largest chip procurement agreements in history and positions Google to deploy millions of custom accelerators across its global data center footprint. Google has stated a target of operating 5 million TPUs by 2027, a scale that would make its custom silicon deployment the largest in the world outside of Nvidia's ecosystem."),
  body("The strategic rationale is clear: Google processes more AI queries than any other company through its Search, Gemini, and YouTube products. Owning the silicon stack reduces dependency on Nvidia's pricing and supply constraints while enabling hardware-software co-optimization for Google's specific workloads, particularly the Gemini family of large language models."),

  h2("1.3 Microsoft: Maia 100/200 and Azure Silicon Stack"),
  body("Microsoft entered the custom silicon market with the Azure Maia 100 AI accelerator, designed in-house and fabricated on TSMC's 5nm process. The Maia 100 is optimized for large language model inference workloads within Microsoft's Azure cloud infrastructure and is intended to complement rather than replace Nvidia GPUs, providing a cost-efficient option for specific deployment patterns."),
  body("The company is developing the Maia 200, which was originally scheduled for 2026 production on TSMC's 3nm process but has reportedly experienced a six-month delay, pushing volume production into early 2027. Microsoft has also invested in custom ARM-based server CPUs (the Cobalt series) for general compute workloads that complement AI accelerators. Microsoft's total capital expenditure for FY2026 is approximately $75 billion, with a significant portion allocated to AI infrastructure including custom silicon procurement and deployment."),

  h2("1.4 Amazon: Trainium and Inferentia at Scale"),
  body("Amazon Web Services has been developing custom AI chips longer than most hyperscalers. The Inferentia series, focused on inference, and the Trainium series, focused on training, represent Amazon's strategy to reduce both cost and dependency on third-party AI accelerators for its massive cloud AI platform."),
  body("Trainium2, currently in deployment across AWS data centers, delivers 2x the training performance of the original Trainium chip while improving energy efficiency. Amazon has announced Trainium3, expected in 2027, which will target further performance gains. AWS custom chip revenue exceeded $25 billion annually as of early 2026, demonstrating that the strategy of offering both Nvidia-based and custom-silicon-based instances has found strong market adoption."),
  body("Amazon's chip development is supported by Annapurna Labs, an Israeli chip design company acquired in 2015, which has become a critical R&D center for AWS silicon. The company's 2026 capital expenditure of $200 billion -- the largest of any technology company -- includes substantial investment in both custom chip procurement and the data center infrastructure required to deploy them at scale."),

  h2("1.5 Meta: MTIA, Iris, and Broadcom 2nm Partnership"),
  body("Meta has developed four generations of its Meta Training and Inference Accelerator (MTIA), with the latest generation achieving performance levels that make it viable for production AI workloads within Meta's social media and advertising infrastructure. The MTIA is optimized for the recommendation and ranking models that drive Facebook, Instagram, and WhatsApp, as well as increasingly for generative AI features powered by the Llama family of models."),
  body("In 2026, Meta announced Iris, its next-generation AI inference chip scheduled for production in September 2026. More significantly, Meta has signed a major agreement with Broadcom to co-design custom AI chips on TSMC's 2nm process node, representing Meta's most ambitious silicon investment to date. This partnership mirrors the Broadcom deals signed by Google and reflects a broader trend among hyperscalers to leverage Broadcom's chip design expertise while maintaining control over architectural decisions."),

  h2("1.6 Apple: Neural Engine and Server-Side AI Chips"),
  body("Apple, long known for designing custom silicon for consumer devices (the M-series and A-series chips), has entered the AI data center chip market. Reports indicate that Apple plans to produce 5 to 7 million server-grade AI chips in 2026, fabricated by TSMC on a 3nm or 4nm process. These chips, internally code-named Baltra, are designed to power Apple Intelligence features -- including Siri enhancements, on-device and cloud-based generative AI, and image generation -- within Apple's Private Cloud Compute infrastructure."),
  body("Apple's unique advantage is its vertically integrated ecosystem: the same company that designs the iPhone processor also designs the server chip that powers cloud AI features for that iPhone. This enables seamless workload partitioning between on-device inference (using the Neural Engine in Apple Silicon) and cloud inference (using the Baltra server chips), with privacy-preserving architecture that differentiates Apple's approach from competitors. Apple has also invested in domestic chip packaging capacity, including a new facility in Houston, Texas, as part of a broader $500 billion U.S. investment commitment."),

  h2("1.7 AI Chip Startups: Cerebras, Groq, SambaNova, and Tenstorrent"),
  body("Several well-funded startups are challenging the established players with novel architectures. Cerebras Systems, maker of the Wafer-Scale Engine (WSE-3) -- the largest chip ever built at 462.5 square millimeters containing 4 trillion transistors -- raised a $1.1 billion Series G round and has achieved a valuation of approximately $8.1 billion. Cerebras focuses on fast training turnaround, offering what it claims is the fastest time-to-train for large language models by eliminating the communication overhead of traditional multi-GPU clusters."),
  body("Groq, founded by former Google TPU architect Jonathan Ross, raised $650 million in June 2026 and is focused exclusively on ultra-fast inference using its LPU (Language Processing Unit) architecture. Groq's chips achieve extremely low latency for real-time AI applications, positioning the company as a leader in inference-as-a-service. SambaNova, which raised $1 billion at an $11 billion valuation in July 2026, offers full-stack AI systems combining custom chips with software for enterprise AI deployments. Tenstorrent, led by legendary chip architect Jim Keller, raised a $693 million Series D and is reportedly in acquisition discussions with Qualcomm valued at $8-10 billion, reflecting the strategic importance of novel AI chip architectures."),

  h2("1.8 China: Huawei Ascend, SMIC, and Domestic Alternatives"),
  body("Chinese AI chip development continues despite U.S. export restrictions that limit access to advanced semiconductor manufacturing. Huawei's Ascend series, particularly the Ascend 910B and the newer 950PR, serves as the primary domestic alternative to Nvidia GPUs for AI training workloads within China. Huawei's chip division generated approximately $12 billion in revenue in 2026, driven by domestic demand for AI training infrastructure."),
  body("The Ascend chips are fabricated primarily by SMIC (Semiconductor Manufacturing International Corporation), China's leading foundry, which has achieved production capability at 5nm and is working toward 3nm. While SMIC's yields and performance at advanced nodes lag behind TSMC, the geopolitical pressure to develop domestic alternatives has created a captive market for Huawei's AI chips. The Chinese government continues to provide substantial subsidies for domestic semiconductor development, with total public investment in the sector exceeding $50 billion across various national and provincial funds."),

  tableTitle("Table 1: Major AI Chip Investment Summary (2025-2027)"),
  makeTable(
    ["Company", "Chip/Product", "Process Node", "Key Investment / Revenue", "Timeline"],
    [
      ["Nvidia", "Blackwell (B200/GB200)", "4nm TSMC", "$216B FY2026 revenue", "Volume production 2024-2025"],
      ["Nvidia", "Rubin (Next-gen)", "3nm TSMC", "Part of $216B R&D pipeline", "Late 2026 / Early 2027"],
      ["Google", "TPU v7x (Ironwood)", "Custom (Broadcom)", "$46B Broadcom deal", "2026 deployment"],
      ["Google", "TPU fleet expansion", "5nm/4nm", "5M TPUs target by 2027", "2025-2027"],
      ["Microsoft", "Maia 200", "3nm TSMC", "$75B total capex FY2026", "Early 2027 (delayed)"],
      ["Amazon", "Trainium2/3", "Custom (Annapurna)", "$25B+ chip revenue, $200B capex", "Trainium3: 2027"],
      ["Meta", "MTIA v4 / Iris / Broadcom", "2nm TSMC (Broadcom)", "Major Broadcom partnership", "Iris: Sep 2026"],
      ["Apple", "Baltra (server chip)", "3nm/4nm TSMC", "5-7M chips, $500B U.S. plan", "2026 production"],
      ["Cerebras", "WSE-3", "5nm TSMC", "$1.1B Series G, $8.1B val.", "Available now"],
      ["Groq", "LPU Inference", "Custom", "$650M raise (Jun 2026)", "Inference-as-a-service"],
      ["SambaNova", "SN40L", "Custom", "$1B at $11B val. (Jul 2026)", "Enterprise AI systems"],
      ["Tenstorrent", "Grayskull/Raimon", "Custom", "$693M Series D", "Qualcomm $8-10B talks"],
      ["Huawei", "Ascend 950PR", "5nm SMIC", "$12B chip revenue 2026", "Available in China"],
      ["TSMC", "Advanced foundry", "3nm/2nm volume", "$38-42B 2025 capex", "2nm volume 2026"],
    ],
    [18, 22, 15, 25, 20],
  ),
];

const section2_dc = [
  h1("2. Data Center Investment"),
  body("The explosive growth in AI compute demand has transformed data center construction into one of the largest capital deployment activities in the global economy. AI training clusters and inference farms require purpose-built facilities with power densities 5-10x higher than traditional cloud data centers, advanced liquid cooling systems, and proximity to abundant and affordable electricity. The total investment in AI-optimized data center construction in 2026 is estimated to exceed $300 billion globally."),

  h2("2.1 The Stargate Project"),
  body("The Stargate project represents the single largest AI infrastructure investment ever announced. Launched in January 2025 as a joint venture between OpenAI, SoftBank, Oracle, and MGX (a UAE-based investment firm), with subsequent participation from Microsoft and Nvidia, Stargate has committed $500 billion over multiple phases to construct a network of AI supercomputing facilities across the United States."),
  body("Phase 1, currently underway in Abilene, Texas, encompasses 1.2 gigawatts of power capacity with an initial investment of approximately $100 billion. The full project targets 10 gigawatts of total power capacity across multiple sites, which would make it the largest computing installation in human history by a significant margin. Stargate's facilities are designed from the ground up for AI workloads, featuring advanced liquid cooling, direct connections to dedicated power generation, and custom networking infrastructure optimized for the communication patterns of large-scale model training."),
  body("The strategic rationale extends beyond pure compute capacity. By building independent infrastructure, Stargate's backers -- particularly OpenAI -- reduce dependency on the big three cloud providers (AWS, Azure, Google Cloud) and gain negotiating leverage over both compute costs and availability. The project has also attracted significant political support as a demonstration of American leadership in AI infrastructure."),

  h2("2.2 Google Data Center Expansion"),
  body("Google's parent company Alphabet has announced capital expenditure guidance of $185-190 billion for 2026, the overwhelming majority of which is directed toward data center construction and AI infrastructure. This follows $52 billion in 2024 and a projected $75 billion for 2025. Alphabet CEO Sundar Pichai has characterized the company's long-term AI infrastructure investment potential as exceeding $1 trillion, signaling that the current spending pace represents the early stages of a multi-decade buildout."),
  body("Google's data center expansion is global in scope, with significant new facilities under construction in the United States, Europe, Asia, and Latin America. The company is prioritizing sites with access to large-scale renewable energy and favorable regulatory environments. Google's data centers are purpose-built for TPU pods, with custom cooling and networking infrastructure that maximizes the performance of its custom silicon stack."),

  h2("2.3 Amazon AWS AI Data Centers"),
  body("Amazon Web Services has committed to $200 billion in capital expenditure for 2026, representing the largest annual infrastructure investment by any company in the world. A significant portion of this spending is directed toward AI-optimized data centers, including massive new facilities designed for UltraCluster deployments -- AWS's term for large-scale GPU/Trainium clusters used for frontier AI training."),
  body("AWS's data center strategy includes several landmark investments: a $50 billion commitment to federal government cloud infrastructure, including classified and defense AI capabilities; a $48 billion investment in India to establish the region's largest cloud and AI computing footprint; and a network of new AI-specific data centers across the United States, Europe, and Asia-Pacific. Amazon's construction pipeline includes facilities in Virginia, Ohio, Texas, Georgia, and international sites in Japan, Singapore, and the UAE."),

  h2("2.4 Meta Data Center Buildout"),
  body("Meta has committed $125-145 billion in capital expenditure for 2026, continuing the aggressive data center construction pace that began in 2023-2024. The company's cumulative data center investment now exceeds $600 billion, reflecting its position as one of the world's largest operators of AI computing infrastructure. Meta's data centers house the massive GPU clusters used to train the Llama family of open-source large language models, as well as the inference infrastructure serving billions of users across Facebook, Instagram, WhatsApp, and Threads."),
  body("Meta has pioneered several innovations in data center design, including the use of open-rack architectures (through the Open Compute Project) and advanced liquid cooling systems that achieve power usage effectiveness (PUE) ratios significantly below the industry average. The company's newest AI training facilities are designed for power densities exceeding 100 kilowatts per rack, approximately 5x the density of traditional cloud data centers."),

  h2("2.5 Apple Private Cloud Compute"),
  body("Apple's approach to AI data centers differs fundamentally from competitors. Rather than building massive public-facing GPU clusters, Apple is constructing a Private Cloud Compute (PCC) infrastructure designed to process user AI queries while maintaining the company's hallmark focus on user privacy. Apple has partnered with Google Cloud to host some of its PCC infrastructure, leveraging Google's data center footprint while maintaining Apple's cryptographic privacy guarantees."),
  body("Apple's overall capital expenditure commitment of $500 billion for U.S. investment over multiple years includes data center construction, chip manufacturing facilities (including the Houston factory), and supporting infrastructure. The PCC approach reflects Apple's strategic belief that users will favor AI services that demonstrably protect their data, potentially creating a competitive moat as privacy regulations tighten globally."),

  h2("2.6 Cooling Technology and Advanced Facilities"),
  body("The shift to AI-optimized data centers has driven rapid adoption of liquid cooling technologies. Traditional air cooling is insufficient for the power densities of modern AI accelerators -- Nvidia's GB200 rack, for example, requires liquid cooling to operate at full capacity. The AI-specific liquid cooling market reached approximately $3 billion in 2025 and is projected to exceed $6.7 billion by 2027, encompassing direct-to-chip cooling, cold plate systems, and immersion cooling technologies."),
  body("Major technology companies are also investing in edge computing and federated data center architectures that bring AI inference closer to end users, reducing latency for real-time applications. These investments include micro data centers in population centers, content delivery network integrations, and hybrid architectures that combine central AI training clusters with distributed inference nodes."),

  tableTitle("Table 2: Major Data Center Investment Summary (2025-2027)"),
  makeTable(
    ["Company / Project", "2026 Capex / Investment", "Key Locations", "Power Capacity", "Strategic Focus"],
    [
      ["Stargate (OpenAI/SoftBank/Oracle)", "$500B total (multi-phase)", "Abilene, TX (Phase 1)", "10 GW (full build)", "Independent AI supercomputing"],
      ["Alphabet / Google", "$185-190B capex", "Global (US, EU, Asia, LATAM)", "Not disclosed", "TPU pods, Gemini AI workloads"],
      ["Amazon / AWS", "$200B capex", "US, India, Japan, Singapore, UAE", "GW-class per site", "UltraCluster GPU/Trainium"],
      ["Meta", "$125-145B capex", "Global (US, EU, Asia)", "100kW+ per rack", "Llama training, social AI inference"],
      ["Apple", "$500B multi-year U.S. plan", "US (Google Cloud partnership)", "Not disclosed", "Private Cloud Compute, privacy"],
      ["AI Cooling Market", "$6.7B by 2027 (total liquid)", "Global", "N/A", "Direct-to-chip, immersion cooling"],
    ],
    [22, 20, 20, 18, 20],
  ),
];

const section3_energy = [
  h1("3. Energy and Power Infrastructure"),
  body("AI infrastructure is fundamentally constrained by power availability. A single large-scale AI training cluster can consume as much electricity as a small city -- the Stargate project's target of 10 gigawatts would make it one of the largest electricity consumers in the United States. This reality has triggered an unprecedented wave of energy investment by technology companies, spanning nuclear power, renewable energy procurement, experimental fusion, and grid infrastructure upgrades."),

  h2("3.1 Nuclear Energy: The Return to Fission"),
  body("Nuclear power has emerged as the preferred energy source for large-scale AI infrastructure due to its ability to provide massive, reliable, carbon-free baseload electricity. Three major technology companies have signed transformative nuclear energy agreements in 2025-2026."),
  body("Microsoft signed a landmark agreement with Constellation Energy in September 2024 to restart the Three Mile Island Unit 1 nuclear reactor, which had been dormant since 2019. The deal, valued at $1.6 billion, provides Microsoft with 835 megawatts of baseload power under a 20-year power purchase agreement, with the reactor expected to return to commercial operation in 2027. This agreement represents the first major technology-sector investment in reviving dormant nuclear capacity."),
  body("Amazon has pursued an even more aggressive nuclear strategy, signing multiple agreements that collectively exceed 1,920 megawatts of capacity. Amazon's largest deal is with Talen Energy for the Susquehanna nuclear power plant in Pennsylvania, providing approximately 960 megawatts. Additional agreements include partnerships with Energy Northwest and Dominion Energy for nuclear-powered data center campuses. Amazon's total nuclear-related infrastructure investment exceeds $20 billion."),
  body("Google has also entered the nuclear arena, signing an agreement with Kairos Power to deploy small modular reactors (SMRs) to power its data centers, with the first units expected to be operational by 2030. Google's nuclear strategy focuses on next-generation reactor technology, avoiding the long construction timelines and regulatory complexity of traditional large reactors."),

  h2("3.2 Fusion Energy: High-Risk, High-Reward Bets"),
  body("Several technology companies are investing in fusion energy as a long-term solution for AI power demands. Microsoft is the most notable, having signed a power purchase agreement with Helion Energy in 2023 for a fusion-powered data center by 2028. Helion has raised approximately $1.5 billion in total funding, with Microsoft's commitment providing both capital and a guaranteed first customer. Helion's Polaris prototype is designed to demonstrate net energy gain by 2025-2026, with commercial delivery targeted for 2028."),
  body("Commonwealth Fusion Systems (CFS), a spinout from MIT, has raised approximately $4 billion in total funding from investors including Google, Bill Gates, and other technology figures. CFS is building SPARC, a tokamak-based fusion reactor that uses high-temperature superconducting magnets to achieve conditions for net energy production. The company targets a commercial reactor, ARC, by the early 2030s."),
  body("While fusion timelines are inherently uncertain -- the technology has been '30 years away' for decades -- the intensity of recent investment and the involvement of serious technology companies suggest that the risk calculus has shifted. If any fusion company achieves commercial operation, it would fundamentally transform the economics of AGI infrastructure by providing effectively unlimited clean energy."),

  h2("3.3 Power Purchase Agreements and Renewable Energy"),
  body("Beyond nuclear, technology companies have signed a torrent of renewable energy power purchase agreements (PPAs) to support AI infrastructure. The total value of corporate PPAs signed in 2025 exceeded $50 billion globally, with AI-related demand accounting for the majority of new agreements. These PPAs span solar, wind, battery storage, and hybrid renewable-plus-storage projects, typically structured as 10-20 year agreements that provide both price certainty and renewable energy certificates."),
  body("Grid infrastructure investment has become a critical bottleneck. The U.S. power grid, in particular, faces capacity constraints in the regions where AI data centers are being concentrated -- notably Virginia's 'Data Center Alley,' northern Texas, and the Pacific Northwest. Technology companies are increasingly investing directly in grid upgrades, transmission line construction, and substation capacity to ensure their facilities can receive adequate power supply."),

  tableTitle("Table 3: Major Energy Investments for AI Infrastructure"),
  makeTable(
    ["Deal / Company", "Type", "Capacity", "Value / Investment", "Timeline"],
    [
      ["Microsoft - Constellation (TMI)", "Nuclear fission restart", "835 MW", "$1.6B, 20-year PPA", "Commercial 2027"],
      ["Amazon - Talen (Susquehanna)", "Nuclear fission", "960 MW", "$650M campus + $20B+", "Underway"],
      ["Amazon - Energy Northwest", "Nuclear (SMR)", "~480 MW", "Part of $20B+ total", "2030s"],
      ["Amazon - Dominion Energy", "Nuclear-powered campus", "~480 MW", "Part of $20B+ total", "2028-2030"],
      ["Google - Kairos Power", "Nuclear SMR deployment", "500 MW (phased)", "Undisclosed", "2030 (first units)"],
      ["Microsoft - Helion Energy", "Fusion energy PPA", "50 MW (initial)", "$1.5B total raised", "2028 (target)"],
      ["CFS (Commonwealth Fusion)", "Fusion (tokamak)", "Commercial scale", "~$4B total raised", "Early 2030s (ARC)"],
      ["Corporate PPAs (Global)", "Renewable energy", "Varies", "$50B+ signed in 2025", "10-20 year terms"],
    ],
    [22, 18, 15, 20, 25],
  ),
];

const section4_networking = [
  h1("4. Networking and Interconnect Infrastructure"),
  body("AI workloads at scale impose unique and demanding requirements on networking infrastructure. Large language model training, which involves thousands of accelerators operating in parallel, requires extremely high bandwidth and low latency interconnects to maintain efficiency. The networking layer -- encompassing chip-to-chip, server-to-server, and data-center-to-data-center communication -- represents a critical and increasingly valuable segment of AI infrastructure investment."),

  h2("4.1 InfiniBand versus Ethernet: The Interconnect War"),
  body("The AI training interconnect market has been dominated by Nvidia's InfiniBand technology, which offers superior bandwidth and latency characteristics for the all-to-all communication patterns inherent in distributed AI training. However, the Ultra Ethernet Consortium (UEC), backed by AMD, Intel, Meta, Microsoft, Google, Amazon, Cisco, and other major players, is developing an open-standard Ethernet-based alternative that aims to match InfiniBand performance at lower cost."),
  body("The market is shifting toward Ethernet for inference workloads, where cost efficiency matters more than absolute latency. Training clusters, particularly at the frontier model scale, continue to favor InfiniBand due to its proven performance at scale. Nvidia's networking division generated $7.3 billion in revenue in FY2026, reflecting the premium pricing that InfiniBand commands for AI training deployments. The outcome of the InfiniBand versus Ethernet competition will have significant implications for the cost structure of AGI infrastructure over the next decade."),

  h2("4.2 Optical Networking: 800G and 1.6T Transceivers"),
  body("The rapid growth in AI cluster scale has driven demand for high-speed optical transceivers for data center interconnects. The market for AI-related optical networking components reached approximately $4.5 billion in 2025, with 800 gigabit-per-second (800G) transceivers as the dominant standard and 1.6 terabit-per-second (1.6T) transceivers beginning volume production in 2026."),
  body("Companies including Coherent, Lumentum, Broadcom, and Cisco are investing heavily in next-generation optical components. The transition from 400G to 800G, and now to 1.6T, is being driven by the bandwidth requirements of AI training clusters, where each GPU generates and consumes enormous volumes of data during the training process. The total addressable market for AI optical networking is projected to exceed $10 billion by 2028."),

  h2("4.3 Submarine Cables and Global Connectivity"),
  body("AI infrastructure investment has extended to submarine cable networks, the physical backbone of global internet connectivity. Meta (formerly Facebook) announced the Waterworth project in 2025, a $10 billion submarine cable initiative that will connect the United States, Europe, Africa, Asia, and Australia with the highest-capacity undersea cables ever deployed. Waterworth represents Meta's largest single infrastructure investment outside of data centers and is driven by the need to support AI inference at global scale with minimal latency."),
  body("Google has been a major investor in submarine cables for over a decade, with projects including Curie (connecting Chile to the U.S.), Dunant (U.S. to Europe), and Equiano (connecting Europe to Africa). The total investment in submarine cables by technology companies in 2025-2026 exceeds $13 billion, reflecting the strategic importance of owning the physical connectivity layer between AI data centers and end users worldwide."),

  h2("4.4 Satellite Internet and Remote Infrastructure"),
  body("SpaceX's Starlink satellite constellation has emerged as an important enabler for AI infrastructure in regions where traditional broadband connectivity is insufficient. While not a direct investment in AI compute, satellite internet expands the addressable market for AI services and enables data collection from remote locations for embodied AI and autonomous systems training. Amazon's Project Kuiper, a competing satellite constellation, is under development and expected to begin service in 2026-2027, further expanding global connectivity for AI-enabled applications."),

  tableTitle("Table 4: Networking Infrastructure Investment Summary"),
  makeTable(
    ["Segment", "Key Technology / Project", "Market Size / Investment", "Major Players", "Trend"],
    [
      ["AI Interconnect", "InfiniBand vs. UEC Ethernet", "$7.3B Nvidia networking", "Nvidia, AMD, Intel, Cisco", "Ethernet gaining for inference"],
      ["Optical Transceivers", "800G dominant, 1.6T emerging", "$4.5B (2025)", "Coherent, Lumentum, Broadcom", "$10B+ by 2028"],
      ["Submarine Cables", "Meta Waterworth project", "$13B total (2025-2026)", "Meta ($10B), Google", "Highest capacity ever"],
      ["Satellite Internet", "Starlink / Project Kuiper", "$10B+ combined", "SpaceX, Amazon (Kuiper)", "Expanding AI access globally"],
    ],
    [18, 22, 20, 20, 20],
  ),
];

const section5_data = [
  h1("5. Data Acquisition and Curation"),
  body("The quality and quantity of training data has become a critical strategic asset in the race toward AGI. As large language models scale, the demand for high-quality, diverse, and legally defensible training data has intensified, creating a multi-billion-dollar market for data licensing, synthetic data generation, data labeling, and embodied data collection. Companies are pursuing data strategies with the same urgency as hardware and energy investments, recognizing that algorithmic advantages are increasingly dependent on data advantages."),

  h2("5.1 Training Data Licensing Deals"),
  body("The market for training data licensing has grown rapidly, with individual deals ranging from $5 million to $250 million annually. The most publicized agreement is the Reddit-Google partnership, in which Google pays approximately $60 million per year for access to Reddit's user-generated content for AI training. Similar deals have been signed with other content platforms, social media companies, and publishers."),
  body("The total value of the training data licensing market is estimated to have exceeded $2 billion in 2025 and continues to grow. Technology companies are pursuing these agreements to ensure access to diverse, human-generated text that cannot be replicated by synthetic data, which still struggles with certain types of reasoning and cultural knowledge. Legal frameworks around training data copyright remain unsettled, with multiple lawsuits in progress that could reshape the data acquisition landscape."),

  h2("5.2 Synthetic Data: The Growing Ecosystem"),
  body("Synthetic data -- data generated by AI models rather than collected from human sources -- has emerged as a critical supplement to human-generated training data. The synthetic data market reached approximately $635.6 million in 2026 and is projected to grow at over 30% annually. Synthetic data is particularly valuable for training in domains where real data is scarce, expensive, or privacy-sensitive, such as medical imaging, autonomous driving edge cases, and multilingual language modeling."),
  body("The most significant synthetic data acquisition was Nvidia's purchase of Gretel.ai for approximately $320 million. Gretel.ai specializes in generating high-fidelity synthetic datasets that preserve the statistical properties of real data while protecting individual privacy. Nvidia's acquisition reflects a strategic bet that synthetic data will become an essential component of AI training pipelines, particularly for enterprise customers in regulated industries."),

  h2("5.3 Data Labeling and Annotation"),
  body("Human data labeling remains essential for training and evaluating AI models, particularly for fine-tuning, reinforcement learning from human feedback (RLHF), and safety evaluation. Scale AI, the market leader in AI data labeling, achieved a valuation of approximately $14 billion following a funding round that included Meta acquiring a 49% stake -- one of the largest investments in the data labeling sector. Scale AI provides labeling services for image, text, audio, and video data, with specialized offerings for autonomous vehicle data and medical imaging."),
  body("The global data labeling market, encompassing companies including Scale AI, Labelbox, V7, and numerous regional providers, is estimated at $1.89 billion to $2.32 billion in 2026. Demand is driven by the need for high-quality human annotations to train increasingly capable AI systems, with particular growth in multimodal data labeling (text + image + video) required for next-generation models."),

  h2("5.4 Embodied Data: Robotaxis and Physical AI"),
  body("The development of embodied AI -- AI systems that interact with the physical world -- has created a new category of training data with enormous strategic value. Waymo, Alphabet's autonomous driving subsidiary, operates the world's largest robotaxi fleet with approximately 500,000 paid rides per week across San Francisco, Phoenix, Los Angeles, and Austin. Each ride generates detailed sensor data (lidar, camera, radar) and behavioral data that is invaluable for training autonomous driving systems and, more broadly, for developing AI that understands physical environments."),
  body("Tesla's Full Self-Driving program similarly collects driving data from millions of vehicles globally, creating what is arguably the world's largest dataset of real-world driving behavior. Other embodied data sources include Boston Dynamics' robot operations, Amazon's warehouse robotics, and various humanoid robot prototypes from companies including Figure AI, Agility Robotics, and Tesla's Optimus program."),

  h2("5.5 Copyright and Settlement Funds"),
  body("The legal landscape around AI training data remains contentious. Anthropic, the AI company behind Claude, agreed to a $1.5 billion settlement fund to address copyright claims from content creators, establishing a potential precedent for how AI companies will compensate rights holders whose work was used in training data. Multiple other lawsuits are in progress, including cases brought by The New York Times, music publishers, and various author groups against AI companies."),
  body("The resolution of these legal questions will have significant implications for the economics of AGI development. If courts impose substantial licensing requirements on training data, the cost of training frontier AI models could increase dramatically, creating a moat for companies that have already secured comprehensive data licensing agreements."),

  tableTitle("Table 5: Data Acquisition and Curation Investment Summary"),
  makeTable(
    ["Segment", "Key Deal / Company", "Value / Investment", "Key Details", "Strategic Rationale"],
    [
      ["Data Licensing", "Reddit-Google", "$60M/year", "User content for training", "Diverse human-generated text"],
      ["Data Licensing", "Various publishers", "$5M-$250M per deal", "Text, image, video", "Legal, high-quality data"],
      ["Synthetic Data", "Gretel.ai (Nvidia)", "~$320M acquisition", "Privacy-preserving gen.", "Enterprise regulated data"],
      ["Synthetic Data", "Market total (2026)", "$635.6M market", "30%+ CAGR", "Scarcity supplement"],
      ["Data Labeling", "Scale AI", "$14B valuation, Meta 49%", "1.89B-2.32B total market", "RLHF, fine-tuning, safety"],
      ["Embodied Data", "Waymo", "500K weekly rides", "Lidar/camera/radar", "Largest robotaxi fleet"],
      ["Embodied Data", "Tesla FSD", "Millions of vehicles", "Real-world driving data", "Largest driving dataset"],
      ["Copyright", "Anthropic settlement", "$1.5B fund", "Creator compensation", "Legal precedent setting"],
    ],
    [16, 18, 18, 22, 26],
  ),
];

const section6_cloud = [
  h1("6. Cloud AI Platform Investment"),
  body("Cloud AI platforms represent the primary interface between AGI capabilities and enterprise customers, developers, and end users. The major hyperscalers and specialized GPU cloud providers are investing tens of billions of dollars annually in platform development, model hosting, inference infrastructure, and developer tools. The cloud AI platform market has become the central battleground for AGI commercialization, with each provider seeking to establish its platform as the default environment for building, deploying, and scaling AI applications."),

  h2("6.1 AWS Bedrock"),
  body("Amazon Web Services' Bedrock platform has established itself as the most widely adopted enterprise AI cloud service, serving over 100,000 organizations globally. Bedrock provides access to a curated selection of foundation models -- including Anthropic's Claude, Meta's Llama, Amazon's own Titan models, and models from Mistral, Cohere, and other partners -- through a unified API that abstracts the complexity of model deployment and infrastructure management."),
  body("AWS's investment in Bedrock encompasses model hosting infrastructure (including custom silicon instances powered by Trainium and Inferentia), guardrail and safety tools, RAG (Retrieval-Augmented Generation) integration with Amazon's broader cloud services, and enterprise-grade security and compliance certifications. The platform's breadth of model offerings and deep integration with the AWS ecosystem positions it as the default choice for enterprises already committed to the AWS cloud."),

  h2("6.2 Google Cloud: Gemini Enterprise Agent Platform"),
  body("Google Cloud underwent a significant rebranding at Google Cloud Next 2026, positioning its AI offering as the Gemini Enterprise Agent Platform. This reflects Google's strategic pivot from selling individual AI models to providing a comprehensive platform for building autonomous AI agents that can execute multi-step tasks, access enterprise data, and interact with external systems."),
  body("Google Cloud's revenue reached $24.8 billion in Q2 2026, representing an 82% year-over-year increase driven overwhelmingly by AI platform adoption. The Gemini Enterprise Agent Platform leverages Google's custom TPU infrastructure and the Gemini family of models, offering capabilities in multimodal understanding, code generation, scientific reasoning, and enterprise search. Google's strategy is to differentiate through the quality of its models and the depth of integration with Google's productivity suite (Docs, Sheets, Gmail) and enterprise data services."),

  h2("6.3 Microsoft Azure AI Foundry"),
  body("Microsoft Azure's AI platform, rebranded as AI Foundry (and later Microsoft Foundry), is built around OpenAI's GPT-4 and GPT-5 families of models alongside Microsoft's own Phi series of small language models. Azure's AI infrastructure supports an estimated $13 billion annual run rate for AI services, making it the second-largest cloud AI platform by revenue."),
  body("Microsoft's $75 billion annual capital expenditure directly supports Azure AI infrastructure, including massive GPU clusters for model training and inference. The company's close partnership with OpenAI -- which operates a dedicated Azure supercompute cluster -- provides Azure with access to frontier models that are often available on Azure before competing platforms. Microsoft's integration of AI capabilities into its productivity suite (Copilot for Office 365, GitHub Copilot) drives significant platform adoption."),

  h2("6.4 Nvidia NIM and DGX Cloud"),
  body("Nvidia has extended its silicon dominance into cloud services through NIM (Nvidia Inference Microservices) and DGX Cloud. NIM provides pre-optimized inference containers for Nvidia GPUs that simplify deployment of AI models in production, while DGX Cloud offers managed access to DGX supercomputing clusters for AI training workloads. Together, these services represent Nvidia's strategy to capture value beyond chip sales by controlling the software layer that sits on top of its hardware."),
  body("NIM has been adopted by major cloud providers and enterprises as a standard way to deploy AI models on Nvidia infrastructure, reinforcing Nvidia's ecosystem lock-in. DGX Cloud partnerships with AWS, Azure, Google Cloud, and Oracle provide customers with on-demand access to the most powerful AI training hardware without requiring upfront capital investment."),

  h2("6.5 Oracle AI Cloud and Stargate"),
  body("Oracle has positioned itself as a major AI infrastructure provider through its Oracle Cloud Infrastructure (OCI) and its participation in the Stargate project. Oracle's AI cloud offers Nvidia GPU instances at prices that are typically 20-30% below competing cloud providers, a strategy that has attracted cost-sensitive enterprise customers and AI startups. Oracle's total capital expenditure for 2026 is approximately $50 billion, with a significant allocation to AI infrastructure including a Stargate data center campus providing 1.2 gigawatts of power."),
  body("Oracle's AI cloud strategy leverages its strong relationships with large enterprise customers (particularly in financial services, healthcare, and government) who already run Oracle databases and applications, making it relatively easy to add AI capabilities to existing deployments. The Stargate partnership provides Oracle with access to the largest AI computing installation in the world, further strengthening its infrastructure position."),

  h2("6.6 Specialized GPU Clouds: CoreWeave and Lambda Labs"),
  body("Beyond the major hyperscalers, a category of specialized GPU cloud providers has emerged to serve customers who need large-scale GPU access with greater flexibility, performance optimization, or cost efficiency than the major clouds offer."),
  body("CoreWeave, which specializes in Nvidia GPU infrastructure, achieved $982 million in revenue in Q1 2025 (a 420% year-over-year increase) and completed its IPO in late 2025. The company's success reflects strong demand from AI startups and enterprises that need dedicated GPU clusters with high-performance networking and storage. Lambda Labs, another specialized GPU cloud provider, raised a $1.5 billion Series E and is targeting an IPO in the first half of 2026. Lambda differentiates through its focus on AI training workloads and its development of custom GPU server hardware optimized for large-scale model training."),

  tableTitle("Table 6: Cloud AI Platform Investment Summary"),
  makeTable(
    ["Platform / Company", "Key Metric", "2026 Investment / Revenue", "Model Access", "Competitive Position"],
    [
      ["AWS Bedrock", "100K+ organizations", "Part of $200B capex", "Claude, Llama, Titan, Mistral", "Market leader, breadth"],
      ["Google Cloud (Gemini)", "$24.8B Q2 2026 (+82%)", "$185-190B capex", "Gemini (Google models)", "Rebranded as Agent Platform"],
      ["Azure AI Foundry", "$13B AI run-rate", "$75B capex", "GPT-4/5, Phi (OpenAI)", "OpenAI exclusive, Copilot"],
      ["Nvidia NIM / DGX Cloud", "$7.3B networking rev.", "Part of $216B revenue", "Model-agnostic (Nvidia)", "Ecosystem lock-in"],
      ["Oracle OCI + Stargate", "$50B capex", "Stargate 1.2 GW campus", "Cohere, Nvidia, various", "Price advantage, enterprise"],
      ["CoreWeave", "$982M Q1 2025 (+420%)", "IPO late 2025", "Nvidia GPU specialist", "Pure-play GPU cloud"],
      ["Lambda Labs", "$1.5B Series E", "IPO H1 2026 target", "Nvidia, custom hardware", "AI training optimized"],
    ],
    [18, 20, 18, 22, 22],
  ),
];

const conclusions = [
  h1("7. Conclusions and Strategic Implications"),
  body("The investment landscape for AGI infrastructure in 2026 reveals several critical strategic dynamics that will shape the trajectory of artificial intelligence development over the coming decade."),

  h2("7.1 Unprecedented Capital Intensity"),
  body("The combined annual capital expenditure of the major AGI infrastructure investors now exceeds $600 billion, a figure that surpasses the GDP of many nations. This level of investment is without historical precedent in the technology sector and reflects a collective judgment among the world's most successful technology leaders that AGI is both achievable and commercially transformative. The willingness to commit hundreds of billions of dollars to infrastructure -- much of it with multi-decade payback periods -- signals extraordinary confidence in the economic value of artificial general intelligence."),

  h2("7.2 Vertical Integration as Competitive Moat"),
  body("Every major AGI investor is pursuing vertical integration across the infrastructure stack: custom silicon, proprietary data centers, dedicated energy sources, and owned cloud platforms. This integration strategy reduces dependency on third-party suppliers, enables hardware-software co-optimization, and creates cost advantages that compound at scale. The parallel investments by Google, Amazon, Meta, and Microsoft in both custom chips (via Broadcom partnerships) and proprietary data centers represent the most significant vertical integration in technology since Apple's creation of the iPhone hardware-software ecosystem."),

  h2("7.3 Energy as the Ultimate Constraint"),
  body("Energy availability has emerged as the binding constraint on AGI infrastructure scaling. The aggressive pursuit of nuclear energy, fusion investments, and massive renewable energy PPAs reflects a recognition that compute capacity is ultimately limited by power supply. The technology sector's re-embrace of nuclear power -- after decades of decline -- may prove to be one of the most consequential infrastructure shifts of the 21st century, with implications extending far beyond AI to climate change and global energy security."),

  h2("7.4 The Data Imperative"),
  body("As model architectures converge and compute becomes more commoditized, data quality and diversity are becoming the primary differentiators. Companies that have secured comprehensive training data licensing agreements, built synthetic data generation capabilities, and collected unique embodied data are positioned to maintain competitive advantages even as compute costs decline. The legal resolution of training data copyright questions will be among the most consequential policy decisions affecting AGI development."),

  h2("7.5 Market Structure and Implications"),
  body("The AGI infrastructure market is consolidating into a small number of very large players with the capital, technical expertise, and risk tolerance to compete at frontier scale. Nvidia's chip dominance, the hyperscalers' vertical integration, and the Stargate project's independent infrastructure collectively create a market structure that may resist disruption. Startups and new entrants will need to identify specific niches -- inference optimization, domain-specific models, or novel architectures -- where they can create value against well-capitalized incumbents. The strategic implications for investors, policymakers, and technology leaders are profound: AGI infrastructure is no longer a speculative bet but a massive, ongoing commitment of capital and engineering resources that is reshaping the global technology landscape."),
];

// ─── ASSEMBLE DOCUMENT ───
const doc = new Document({
  styles: {
    default: {
      document: {
        run: {
          font: { ascii: "Times New Roman", eastAsia: "SimSun" },
          size: 24, color: "000000",
        },
        paragraph: {
          spacing: { line: 312 },
        },
      },
      heading1: {
        run: {
          font: { ascii: "Times New Roman", eastAsia: "SimHei" },
          size: 32, bold: true, color: "0A1628",
        },
        paragraph: {
          spacing: { before: 480, after: 200, line: 312 },
          alignment: AlignmentType.CENTER,
        },
      },
      heading2: {
        run: {
          font: { ascii: "Times New Roman", eastAsia: "SimHei" },
          size: 28, bold: true, color: "0A1628",
        },
        paragraph: {
          spacing: { before: 360, after: 160, line: 312 },
        },
      },
      heading3: {
        run: {
          font: { ascii: "Times New Roman", eastAsia: "SimHei" },
          size: 24, bold: true, color: "0A1628",
        },
        paragraph: {
          spacing: { before: 240, after: 120, line: 312 },
        },
      },
    },
  },
  sections: [
    // COVER SECTION
    {
      properties: {
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 0, bottom: 0, left: 0, right: 0 },
        },
      },
      children: buildCoverR1(coverConfig),
    },
    // TOC SECTION
    {
      properties: {
        type: SectionType.NEXT_PAGE,
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1440, bottom: 1440, left: 1701, right: 1417 },
        },
      },
      headers: {
        default: new Header({
          children: [new Paragraph({
            alignment: AlignmentType.RIGHT,
            children: [new TextRun({ text: "AGI Infrastructure Investment Report | August 2026", size: 16, color: "888888",
              font: { ascii: "Calibri", eastAsia: "Microsoft YaHei" } })],
          })],
        }),
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "888888",
              font: { ascii: "Calibri" } })],
          })],
        }),
      },
      children: [
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 480, after: 360 },
          children: [new TextRun({
            text: "Table of Contents", bold: true, size: 32, color: "0A1628",
            font: { ascii: "Times New Roman", eastAsia: "SimHei" },
          })],
        }),
        new TableOfContents("Table of Contents", {
          hyperlink: true,
          headingStyleRange: "1-3",
        }),
        new Paragraph({
          spacing: { before: 200 },
          children: [new TextRun({
            text: 'Note: This Table of Contents is generated via field codes. To ensure page number accuracy after editing, please right-click the TOC and select "Update Field."',
            italics: true, size: 18, color: "888888",
            font: { ascii: "Times New Roman" },
          })],
        }),
        new Paragraph({ children: [new PageBreak()] }),
      ],
    },
    // BODY SECTION
    {
      properties: {
        type: SectionType.NEXT_PAGE,
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1440, bottom: 1440, left: 1701, right: 1417 },
        },
      },
      headers: {
        default: new Header({
          children: [new Paragraph({
            alignment: AlignmentType.RIGHT,
            children: [new TextRun({ text: "AGI Infrastructure Investment Report | August 2026", size: 16, color: "888888",
              font: { ascii: "Calibri", eastAsia: "Microsoft YaHei" } })],
          })],
        }),
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "888888",
              font: { ascii: "Calibri" } })],
          })],
        }),
      },
      children: [
        h1("Executive Summary"),
        ...executiveSummary,
        ...section1_chips,
        ...section2_dc,
        ...section3_energy,
        ...section4_networking,
        ...section5_data,
        ...section6_cloud,
        ...conclusions,
      ],
    },
  ],
});

// ─── GENERATE FILE ───
const OUTPUT = "F:\\backup\\AGI_Infrastructure_Investment_Report_Aug2026.docx";
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUTPUT, buf);
  console.log("Document generated successfully: " + OUTPUT);
}).catch((err) => {
  console.error("Error generating document:", err);
  process.exit(1);
});
