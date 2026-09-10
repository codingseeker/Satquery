export const SIH_PROBLEM_STATEMENT = {
  id: 'SIH26167',
  hackathon: 'Smart India Hackathon 2026',
  description:
    'SatQuery AI: An agentic vision-language assistant for multimodal remote-sensing image analysis. ' +
    'The goal is to provide a conversational interface for satellite imagery that supports ' +
    'visual question answering (VQA), change detection, multi-sensor (optical/SAR) fusion, ' +
    'and agentic workflows for complex geospatial tasks.',
};

export const EXAMPLE_PROMPTS = [
  {
    category: 'Scene Analysis',
    prompts: [
      'Describe what is visible in this satellite image.',
      'What land cover types are present in this image?',
      'Identify the main features in this scene.',
    ],
  },
  {
    category: 'Change Detection',
    prompts: [
      'What changed between these two images?',
      'Has the built-up area increased since the earlier image?',
      'Identify areas of vegetation loss in this temporal pair.',
    ],
  },
  {
    category: 'Water & Terrain',
    prompts: [
      'Locate and highlight the water bodies in this image.',
      'Identify areas affected by flooding.',
    ],
  },
];
