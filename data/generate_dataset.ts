/**
 * Generates synthetic training data from the existing deterministic generator.
 *
 * Run:  npx tsx generate_dataset.ts
 * Deps: Must be run from the AI/data/ directory with the Website available at ../../Website
 */

import { generateBuild } from '../../Website/src/engine/generator';
import type { BuildCategory, BuildData } from '../../Website/src/engine/buildSchema';
import { writeFileSync } from 'fs';
import { resolve } from 'path';

const CATEGORIES: BuildCategory[] = [
  'house', 'factory', 'village', 'castle',
  'temple', 'treehouse', 'bridge', 'trainstation',
];

const BLOCK_PALETTE = [
  'Stone', 'Oak Log', 'Oak Planks', 'Cobblestone', 'Bricks',
  'Glass', 'Sand', 'Iron Block', 'Gold Block', 'Dirt',
  'Wool', 'Obsidian', 'Quartz Block', 'Sandstone',
  'Spruce Planks', 'Birch Planks', 'Acacia Planks', 'Dark Oak Planks',
];

const DESCRIPTIONS: Record<BuildCategory, string[]> = {
  house: [
    'A cozy cottage with a chimney',
    'Modern minimalist home',
    'Rustic log cabin in the woods',
    'Two-story farmhouse with a porch',
    'Small stone dwelling with garden',
    'Thatched-roof village hut',
    'Hillside hobbit hole',
    'Beach house on stilts',
  ],
  factory: [
    'Steam-powered iron foundry',
    'Redstone processing plant',
    'Automated crop harvester building',
    'Dark industrial smelting facility',
    'Wool dyeing workshop',
    'Large mining operation headquarters',
    'Potion brewing factory',
    'Enchantment assembly line building',
  ],
  village: [
    'Peaceful farming hamlet',
    'Medieval trading post settlement',
    'Desert oasis village',
    'Snowy mountain community',
    'Coastal fishing village',
    'Forest clearing settlement',
    'Plains farming village',
    'Hillside terraced community',
  ],
  castle: [
    'Grand medieval fortress',
    'Dark gothic stronghold',
    'Royal palace with towers',
    'Mountain-top citadel',
    'Coastal defense fort',
    'Ruined ancient keep',
    'Dwarven stone fortress',
    'Fairy tale princess castle',
  ],
  temple: [
    'Ancient Greek marble temple',
    'Jungle ruin temple',
    'Desert sandstone pyramid shrine',
    'Underwater ocean monument',
    'Mountain monastery',
    'Nether wart shrine',
    'End stone sanctuary',
    'Ice palace temple',
  ],
  treehouse: [
    'Elven canopy dwelling',
    'Jungle treehouse with rope bridges',
    'Giant oak platform house',
    'Enchanted forest hideout',
    'Multi-level tree village',
    'Dark oak canopy base',
    'Spruce treetop observatory',
    'Birch grove tree shelter',
  ],
  bridge: [
    'Roman-style stone aqueduct',
    'Covered wooden bridge',
    'Grand suspension bridge',
    'Medieval drawbridge',
    'Simple plank footbridge',
    'Decorative garden bridge',
    'Industrial rail bridge',
    'Ancient stone arch bridge',
  ],
  trainstation: [
    'Victorian-era grand station',
    'Small countryside rail stop',
    'Underground metro station',
    'Industrial cargo terminal',
    'Mountain pass railway station',
    'Desert junction stop',
    'Coastal harbour terminal',
    'Modern high-speed rail hub',
  ],
};

const WIDTH_RANGE = { min: 8, max: 40 };
const HEIGHT_RANGE = { min: 6, max: 25 };

interface TrainingExample {
  prompt: string;
  completion: string;
}

function pickRandom<T>(arr: T[], rng: () => number): T {
  return arr[Math.floor(rng() * arr.length)];
}

function pickBlocks(rng: () => number): string[] {
  const count = 1 + Math.floor(rng() * 3);
  const shuffled = [...BLOCK_PALETTE].sort(() => rng() - 0.5);
  return shuffled.slice(0, count);
}

function encodeBuild(build: BuildData): string {
  const uniqueTypes = [...new Set(build.blocks.map(b => b.type))];
  const legend: Record<string, string> = {};
  uniqueTypes.forEach((t, i) => legend[t] = String.fromCharCode(65 + i));

  const lines: string[] = [];
  const d = build.dimensions;
  lines.push(`DIM:${d.width}x${d.height}x${d.depth}`);

  const legendStr = Object.entries(legend).map(([k, v]) => `${v}=${k}`).join(',');
  lines.push(`T:${legendStr}`);

  for (const block of build.blocks) {
    lines.push(`${block.x},${block.y},${block.z},${legend[block.type]}`);
  }

  return lines.join('\n');
}

function buildPrompt(
  description: string,
  category: string,
  blocks: string[],
  width: number,
  height: number,
): string {
  return [
    `Generate a Minecraft ${category} build.`,
    `Description: ${description}`,
    `Blocks: ${blocks.join(', ')}`,
    `Width: ${width}, Height: ${height}`,
    `Output the build in compact block format.`,
  ].join('\n');
}

/** Simple mulberry32 seeded RNG. */
function seededRng(seed: number): () => number {
  return function () {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function main() {
  const examples: TrainingExample[] = [];
  let globalSeed = 42;

  for (const category of CATEGORIES) {
    const descs = DESCRIPTIONS[category];

    for (const desc of descs) {
      // Generate several variations per description
      for (let variation = 0; variation < 8; variation++) {
        const rng = seededRng(globalSeed++);
        const blocks = pickBlocks(rng);
        const width = WIDTH_RANGE.min + Math.floor(rng() * (WIDTH_RANGE.max - WIDTH_RANGE.min));
        const height = HEIGHT_RANGE.min + Math.floor(rng() * (HEIGHT_RANGE.max - HEIGHT_RANGE.min));

        const build = generateBuild({ description: desc, category, blocks, width, height });
        const prompt = buildPrompt(desc, category, blocks, width, height);
        const completion = encodeBuild(build);

        examples.push({ prompt, completion });
      }
    }
  }

  console.log(`Generated ${examples.length} training examples`);

  const jsonlLines = examples.map(ex => JSON.stringify(ex));
  const outputPath = resolve(__dirname, 'dataset.jsonl');
  writeFileSync(outputPath, jsonlLines.join('\n'), 'utf-8');
  console.log(`Wrote dataset to ${outputPath}`);
}

main();
