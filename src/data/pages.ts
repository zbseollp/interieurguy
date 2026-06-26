export interface PageData {
  slug: string;
  title: string;
  description: string;
  featuredImage: string;
  content: string;
  type: 'article' | 'product' | 'category' | 'page' | 'blog';
  url: string;
  items?: { label: string; href: string }[];
}

import pagesJson from './pages.json';
import slugsJson from './slugs.json';
import { mainNavigation } from './navigation';

export const pages = pagesJson as Record<string, PageData>;
export const allSiteSlugs = slugsJson as string[];

export function getPage(slug: string): PageData | undefined {
  return pages[slug];
}

export function getCategoryItems(slug: string) {
  const navItem = mainNavigation.find((item) => item.href === `/${slug}/`);
  if (!navItem?.children) return [];
  return navItem.children.map((child) => ({
    title: child.label,
    href: child.href,
    image: '/images/2023/07/1-2.jpg',
    alt: child.label,
  }));
}
