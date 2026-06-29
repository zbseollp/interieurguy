function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
    .slice(0, 80);
}

function extractImage(node: Element | null): HTMLImageElement | null {
  if (!node) return null;
  if (node.tagName === 'IMG') return node as HTMLImageElement;
  if (node.tagName === 'P') return node.querySelector('img');
  return null;
}

function removeInhoudsopgaveBlock(container: HTMLElement) {
  const tocHeading = [...container.querySelectorAll('h4')].find(
    (h) => h.textContent?.trim() === 'Inhoudsopgave'
  );
  if (!tocHeading) return;

  let next = tocHeading.nextElementSibling;
  while (next && next.tagName !== 'H4') {
    const toRemove = next;
    next = next.nextElementSibling;
    toRemove.remove();
  }
  tocHeading.remove();
}

function wrapProductCards(container: HTMLElement) {
  const headings = [...container.querySelectorAll(':scope > h2')];

  for (const heading of headings) {
    if (!/^\d+\./.test(heading.textContent?.trim() ?? '')) continue;

    let img: HTMLImageElement | null = null;
    let prev = heading.previousElementSibling;
    while (prev && prev.tagName !== 'H2') {
      const found = extractImage(prev);
      if (found) {
        img = found;
        found.remove();
        if (!prev.textContent?.trim() && !prev.querySelector('img')) {
          prev.remove();
        }
        break;
      }
      prev = prev.previousElementSibling;
    }

    const contentNodes: Element[] = [];
    let sibling = heading.nextElementSibling;
    while (sibling && sibling.tagName !== 'H2') {
      contentNodes.push(sibling);
      sibling = sibling.nextElementSibling;
    }

    const card = document.createElement('div');
    card.className = 'product-card';
    const inner = document.createElement('div');
    inner.className = 'product-card__inner';
    const media = document.createElement('div');
    media.className = 'product-card__media';
    const content = document.createElement('div');
    content.className = 'product-card__content';

    heading.parentNode?.insertBefore(card, heading);
    card.append(inner);
    inner.append(media, content);
    if (img) media.appendChild(img);
    content.appendChild(heading);
    contentNodes.forEach((node) => content.appendChild(node));
  }
}

function buildToc(main: HTMLElement, sidebar: HTMLElement) {
  const headings = [...main.querySelectorAll('h2')].filter((h) => h.textContent?.trim());
  if (headings.length === 0) return;

  for (const heading of headings) {
    if (!heading.id) {
      heading.id = slugify(heading.textContent ?? 'section');
    }
  }

  const toc = document.createElement('nav');
  toc.className = 'product-page__toc';
  toc.setAttribute('aria-label', 'Inhoudsopgave');

  const header = document.createElement('div');
  header.className = 'product-page__toc-header';
  header.textContent = 'Inhoudsopgave';

  const list = document.createElement('ol');
  list.className = 'product-page__toc-list';

  for (const heading of headings) {
    const item = document.createElement('li');
    const link = document.createElement('a');
    link.href = `#${heading.id}`;
    link.textContent = heading.textContent?.trim() ?? '';
    item.appendChild(link);
    list.appendChild(item);
  }

  toc.append(header, list);
  sidebar.appendChild(toc);
}

function wrapAuthorBlock(main: HTMLElement) {
  const authorHeading = [...main.querySelectorAll('h4')].find(
    (h) => h.textContent?.trim() === 'Interieur blogger'
  );
  if (!authorHeading) return;

  const block = document.createElement('div');
  block.className = 'product-author';
  authorHeading.parentNode?.insertBefore(block, authorHeading);
  block.appendChild(authorHeading);

  let node = block.nextElementSibling;
  while (node && node.tagName !== 'H2') {
    const next = node.nextElementSibling;
    block.appendChild(node);
    node = next;
  }
}

function splitIntroAndMain(body: HTMLElement, intro: HTMLElement, main: HTMLElement) {
  const splitHeading = [...body.querySelectorAll('h2')].find(
    (h) =>
      h.textContent?.includes('10 van de best') ||
      /^\d+\./.test(h.textContent?.trim() ?? '')
  );

  if (!splitHeading) {
    while (body.firstChild) {
      main.appendChild(body.firstChild);
    }
    return;
  }

  let node = body.firstChild;
  while (node && node !== splitHeading) {
    const next = node.nextSibling;
    intro.appendChild(node);
    node = next;
  }

  while (body.firstChild) {
    main.appendChild(body.firstChild);
  }
}

export function enhanceProductPage() {
  const body = document.querySelector<HTMLElement>('.product-page__body');
  const intro = document.querySelector<HTMLElement>('.product-page__intro-content');
  if (!body || !intro || body.dataset.enhanced === 'true') return;

  body.dataset.enhanced = 'true';

  const layout = document.createElement('div');
  layout.className = 'product-page__layout';
  const main = document.createElement('div');
  main.className = 'product-page__main prose';
  const sidebar = document.createElement('aside');
  sidebar.className = 'product-page__sidebar';

  splitIntroAndMain(body, intro, main);
  removeInhoudsopgaveBlock(main);
  wrapProductCards(main);
  wrapAuthorBlock(main);
  buildToc(main, sidebar);

  layout.append(main, sidebar);
  body.appendChild(layout);
}

if (typeof document !== 'undefined') {
  enhanceProductPage();
}
