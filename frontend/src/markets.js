/** Cascading Directory filters — mirrors backend markets.py; no LLM needed. */
function withOther(places) {
  return [...places, { id: 'Other', label_zh: '其他', label_en: 'Other' }]
}

export const GEO_FILTER_TREE = [
  {
    id: 'APAC',
    label_zh: '亚太 (APAC)',
    label_en: 'Asia-Pacific (APAC)',
    places: withOther([
      { id: 'Singapore', label_zh: '新加坡', label_en: 'Singapore' },
      { id: 'Japan', label_zh: '日本', label_en: 'Japan' },
      { id: 'South Korea', label_zh: '韩国', label_en: 'South Korea' },
      { id: 'Malaysia', label_zh: '马来西亚', label_en: 'Malaysia' },
      { id: 'India', label_zh: '印度', label_en: 'India' },
      { id: 'Indonesia', label_zh: '印度尼西亚', label_en: 'Indonesia' },
      { id: 'China', label_zh: '中国大陆', label_en: 'China' },
      { id: 'Hong Kong', label_zh: '中国香港', label_en: 'Hong Kong, China' },
      { id: 'Taiwan', label_zh: '中国台湾', label_en: 'Taiwan, China' },
      { id: 'Thailand', label_zh: '泰国', label_en: 'Thailand' },
      { id: 'Vietnam', label_zh: '越南', label_en: 'Vietnam' },
      { id: 'Philippines', label_zh: '菲律宾', label_en: 'Philippines' },
      { id: 'Australia', label_zh: '澳大利亚', label_en: 'Australia' },
    ]),
  },
  {
    id: 'NA',
    label_zh: '北美 (NA)',
    label_en: 'North America (NA)',
    places: withOther([
      { id: 'US West Coast', label_zh: '美国西海岸', label_en: 'US West Coast' },
      { id: 'US East Coast', label_zh: '美国东海岸', label_en: 'US East Coast' },
      { id: 'US Central', label_zh: '美国中部', label_en: 'US Central' },
      { id: 'US Territories', label_zh: '美国海外领土', label_en: 'US Territories' },
      { id: 'Canada', label_zh: '加拿大', label_en: 'Canada' },
    ]),
  },
  {
    id: 'LATAM',
    label_zh: '拉美 (LATAM)',
    label_en: 'Latin America (LATAM)',
    places: withOther([
      { id: 'Mexico', label_zh: '墨西哥', label_en: 'Mexico' },
      { id: 'Brazil', label_zh: '巴西', label_en: 'Brazil' },
      { id: 'Argentina', label_zh: '阿根廷', label_en: 'Argentina' },
      { id: 'Colombia', label_zh: '哥伦比亚', label_en: 'Colombia' },
      { id: 'Chile', label_zh: '智利', label_en: 'Chile' },
      { id: 'Peru', label_zh: '秘鲁', label_en: 'Peru' },
    ]),
  },
  {
    id: 'EU',
    label_zh: '欧洲 (EU)',
    label_en: 'Europe (EU)',
    places: withOther([
      { id: 'United Kingdom', label_zh: '英国', label_en: 'United Kingdom' },
      { id: 'France', label_zh: '法国', label_en: 'France' },
      { id: 'Germany', label_zh: '德国', label_en: 'Germany' },
      { id: 'Netherlands', label_zh: '荷兰', label_en: 'Netherlands' },
      { id: 'Ireland', label_zh: '爱尔兰', label_en: 'Ireland' },
      { id: 'Spain', label_zh: '西班牙', label_en: 'Spain' },
      { id: 'Italy', label_zh: '意大利', label_en: 'Italy' },
    ]),
  },
  {
    id: 'MEA',
    label_zh: '中东与非洲 (MEA)',
    label_en: 'Middle East & Africa (MEA)',
    places: withOther([
      { id: 'United Arab Emirates', label_zh: '阿联酋', label_en: 'United Arab Emirates' },
      { id: 'Saudi Arabia', label_zh: '沙特阿拉伯', label_en: 'Saudi Arabia' },
      { id: 'Israel', label_zh: '以色列', label_en: 'Israel' },
      { id: 'Nigeria', label_zh: '尼日利亚', label_en: 'Nigeria' },
      { id: 'South Africa', label_zh: '南非', label_en: 'South Africa' },
      { id: 'Egypt', label_zh: '埃及', label_en: 'Egypt' },
    ]),
  },
]

export function zonesForLocale(locale) {
  const zh = locale === 'zh'
  return GEO_FILTER_TREE.map((z) => ({
    id: z.id,
    label: zh ? z.label_zh : z.label_en,
    places: z.places.map((p) => ({
      id: p.id,
      label: zh ? p.label_zh : p.label_en,
    })),
  }))
}
