export interface NavItem {
  label: string;
  href: string;
  children?: { label: string; href: string }[];
}

export const mainNavigation: NavItem[] = [
  { label: 'Home', href: '/' },
  { label: 'Over ons', href: '/over-ons/' },
  {
    label: 'Meubels',
    href: '/meubels/',
    children: [
      { label: 'Slaapbank met opbergruimte', href: '/beste-slaapbank-met-opbergruimte/' },
      { label: 'Kledingkast met schuifdeuren', href: '/beste-kledingkast-met-schuifdeuren/' },
      { label: 'Kledingkast met spiegel', href: '/beste-kledingkast-met-spiegel/' },
      { label: 'Slaapbank 2 persoons', href: '/beste-slaapbank-2-persoons/' },
      { label: 'Zwevend tv meubel', href: '/beste-zwevend-tv-meubel/' },
      { label: 'Schommelstoelen', href: '/beste-schommelstoelen/' },
      { label: 'Open boekenkast', href: '/beste-open-boekenkast/' },
      { label: 'Bijzettafel hout', href: '/beste-bijzettafel-hout/' },
      { label: 'Tv meubel hout', href: '/beste-tv-meubel-hout/' },
      { label: 'Draaistoel', href: '/beste-draaistoel/' },
    ],
  },
  {
    label: 'Slaapkamer',
    href: '/slaapkamer/',
    children: [
      { label: 'Katoenen dekbedovertrek', href: '/beste-katoenen-dekbedovertrek/' },
      { label: 'Satijnen dekbedovertrek', href: '/beste-satijnen-dekbedovertrek/' },
      { label: 'Elektrische bovendeken', href: '/beste-elektrische-bovendeken/' },
      { label: 'Boxspring met tv lift', href: '/beste-boxspring-met-tv-lift/' },
      { label: 'Digitale wekker', href: '/beste-digitale-wekker/' },
      { label: 'Matras 180×200', href: '/beste-matras-180x200/' },
      { label: 'Luxe boxspring', href: '/beste-luxe-boxspring/' },
      { label: 'Hoeslaken', href: '/beste-hoeslaken/' },
      { label: 'Bedtafel', href: '/beste-bedtafel/' },
      { label: 'Topper', href: '/beste-topper/' },
    ],
  },
  {
    label: 'Elektrische apparaten',
    href: '/elektrische-apparaten/',
    children: [
      { label: 'Robotstofzuiger met dweilfunctie', href: '/beste-robotstofzuiger-met-dweilfunctie/' },
      { label: 'Draadloze home cinema set', href: '/beste-draadloze-home-cinema-set/' },
      { label: 'Wasmachine en droger in 1', href: '/beste-wasmachine-en-droger-in-1/' },
      { label: 'Stoomreiniger laminaat', href: '/beste-stoomreiniger-laminaat/' },
      { label: 'Stoomreiniger vloer', href: '/beste-stoomreiniger-vloer/' },
      { label: 'Inbouw wasmachine', href: '/beste-inbouw-wasmachine/' },
      { label: 'Beamer voor thuis', href: '/beste-beamer-voor-thuis/' },
      { label: 'Robotstofzuiger', href: '/beste-robotstofzuiger/' },
      { label: 'Party speaker', href: '/beste-party-speaker/' },
      { label: 'Platenspeler', href: '/beste-platenspeler/' },
    ],
  },
  { label: 'Laatste berichten', href: '/laatste-berichten/' },
];
