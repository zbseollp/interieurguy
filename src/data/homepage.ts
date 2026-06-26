export interface CardItem {
  title: string;
  href: string;
  image: string;
  alt: string;
  category: string;
  categoryHref?: string;
}

export const heroContent = {
  title: 'De nummer 1 interieurwebsite voor mannen',
  description:
    'Op InterieurGuy.nl vind je de meest uiteenlopende interieurtips om jouw woning nóg meer te laten stralen. Voor elke kamer van je huis hebben wij wel een designtip voor jou in petto. Ook vergelijken wij de nieuwste artikelen op het gebied van interieur en design.',
  backgroundImage: '/images/2023/01/Group-80111.jpg',
};

export const categoryLinks = [
  {
    label: 'Electrische apparatuur',
    href: '/beste-elektrische-haard/',
    icon: '/images/2023/01/icon-park-outline_plug-one1.svg',
  },
  {
    label: 'meubels',
    href: '/beste-open-boekenkast/',
    icon: '/images/2023/01/icon-park-outline_sofa2.svg',
  },
  {
    label: 'Decoratie',
    href: '/beste-glazen-hanglamp/',
    icon: '/images/2023/01/icon-park-outline_four-leaves1.svg',
  },
  {
    label: 'Kunst',
    href: '/beste-luxe-boxspring/',
    icon: '/images/2023/01/icon-park-outline_color-filter1.svg',
  },
  {
    label: 'wandbekleding',
    href: '/beste-droogrek-muur/',
    icon: '/images/2023/01/icon-park-outline_great-wall1.svg',
  },
  {
    label: 'Vloeren',
    href: '/beste-robotstofzuiger-met-dweilfunctie/',
    icon: '/images/2023/01/icon-park-outline_floor-tile1.svg',
  },
] as const;

export const topTenSection = {
  title: 'Top 10 lijstjes',
  description:
    'Ben jij op zoek naar iets specifieks of wil jij gewoon een globaal beeld krijgen aan wat er beschikbaar is aan trendy interieur? Bekijk de top 10 lijstjes per categorie of ga rechstreeks naar de categorie voor welke jij naar op zoek bent.',
};

export const topTenCards: CardItem[] = [
  {
    category: 'Meubels',
    categoryHref: '/meubels/',
    title: 'Zwevend tv meubel',
    href: '/beste-zwevend-tv-meubel/',
    image: '/images/2023/07/1-2.jpg',
    alt: 'meubel',
  },
  {
    category: 'Veiligheid',
    categoryHref: '/veiligheid/',
    title: 'Beveiligingscamera buiten',
    href: '/beste-beveiligingscamera-buiten/',
    image: '/images/2023/07/3.jpg',
    alt: 'Cam',
  },
  {
    category: 'Slaapkamer',
    categoryHref: '/slaapkamer/',
    title: 'Katoenen dekbedovertrek',
    href: '/beste-katoenen-dekbedovertrek/',
    image: '/images/2023/07/4.jpg',
    alt: 'Dekbed',
  },
  {
    category: 'Verwarming',
    title: 'Radiatorombouw',
    href: '/beste-radiatorombouw/',
    image: '/images/2023/07/2.jpg',
    alt: 'Verwarming',
  },
  {
    category: 'Meubels',
    categoryHref: '/meubels/',
    title: 'Open boekenkast',
    href: '/beste-open-boekenkast/',
    image: '/images/2023/07/5.jpg',
    alt: 'Meubels',
  },
  {
    category: 'Elektronica',
    categoryHref: '/elektrische-apparaten/',
    title: 'Stoomreiniger laminaat',
    href: '/beste-stoomreiniger-laminaat/',
    image: '/images/2023/07/Schoonmaak.jpg',
    alt: 'Elektronica',
  },
];

export const aboutSection = {
  title: 'Je huis vormt je basis',
  description:
    'We hebben allemaal een druk leven met allerlei verplichtingen. Juist daarom is het zo ontzettend belangrijk om thuis te komen in een huis waar jij je op je gemak voelt en helemaal tot rust kan komen. Met onze interieur- en designtips richt jij je huis nóg meer naar jouw smaak in. Lees ook onze vergelijkingen van de nieuwste interieurartikelen.',
};

export const reviewsSection = {
  title: 'Laatste reviews',
  description:
    'Wil jij dus een professionele inkijk in wat er op dit moment de trends zijn op het gebied van interieur voor mannen? Lees dan snel verder.',
};

export const latestReviews: CardItem[] = [
  {
    category: 'Review',
    title: 'Prullenbak met sensor',
    href: '/beste-prullenbak-met-sensor/',
    image: '/images/2023/07/ton.jpg',
    alt: 'Prullenbak met sensor',
  },
  {
    category: 'Review',
    title: 'Elektrische haard',
    href: '/beste-elektrische-haard/',
    image: '/images/2023/07/6.jpg',
    alt: 'Elektrische haard',
  },
  {
    category: 'Review',
    title: 'Digitale wekker',
    href: '/beste-digitale-wekker/',
    image: '/images/2023/07/alarm.jpg',
    alt: 'Digitale wekker',
  },
  {
    category: 'Review',
    title: 'Stille mobiele airco',
    href: '/beste-stille-mobiele-airco/',
    image: '/images/2023/07/ac.jpg',
    alt: 'Stille mobiele airco',
  },
  {
    category: 'Review',
    title: 'Bijzettafel hout',
    href: '/beste-bijzettafel-hout/',
    image: '/images/2023/07/tafel.jpg',
    alt: 'Bijzettafel hout',
  },
  {
    category: 'Review',
    title: 'Slimme rookmelder',
    href: '/beste-slimme-rookmelder/',
    image: '/images/2023/07/melder.jpg',
    alt: 'Slimme rookmelder',
  },
];

export const ctaSection = {
  description:
    'Op InterieurGuy.nl vind je de beste reviews van de meest populaire artikelen op het gebied van interieur en design. Wacht dus niet langer en kijk snel welke items niet mogen ontbreken in jouw huis! Mocht je vragen hebben, neem dan contact op via onderstaande knop.',
  ctaLabel: 'Contact opnemen',
  ctaHref: '/contact/',
};
