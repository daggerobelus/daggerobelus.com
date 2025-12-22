import { defineComponent, getText } from '@semantic-ui/component';
import { TailwindPlugin } from '@semantic-ui/tailwind';

const template = await getText('./figure.html');

const defaultSettings = {
  // Image sources - single string or array
  src: '',
  alt: '',

  // For multiple images: array of {src, alt} objects
  images: [],

  // Layout for multiple images: '1x1', '1x2', '2x1', '2x2', 'auto'
  layout: 'auto',

  // Size: 'small', 'medium', 'large', 'full'
  size: 'large',

  // Caption and attribution
  caption: '',
  source: '',
  sourceUrl: '',
};

const createComponent = ({ self, settings }) => ({
  getImages() {
    // If images array provided, use it
    if (settings.images && settings.images.length > 0) {
      return settings.images;
    }
    // Otherwise use single src/alt
    if (settings.src) {
      return [{ src: settings.src, alt: settings.alt }];
    }
    return [];
  },

  getGridClass() {
    const images = self.getImages();
    const count = images.length;
    const layout = settings.layout;

    // Auto-detect layout based on image count
    if (layout === 'auto') {
      if (count === 1) return '';
      if (count === 2) return 'grid grid-cols-2 gap-2';
      if (count === 3) return 'grid grid-cols-3 gap-2';
      if (count === 4) return 'grid grid-cols-2 gap-2';
      return 'grid grid-cols-2 gap-2';
    }

    // Explicit layouts
    const layouts = {
      '1x1': '',
      '1x2': 'grid grid-cols-2 gap-2',
      '2x1': 'grid grid-cols-1 gap-2',
      '2x2': 'grid grid-cols-2 gap-2',
    };

    return layouts[layout] || '';
  },

  getSizeClass() {
    const sizes = {
      small: 'max-w-md mx-auto',
      medium: 'max-w-2xl mx-auto',
      large: 'max-w-4xl mx-auto',
      full: 'w-full -mx-6 md:mx-0',
    };
    return sizes[settings.size] || sizes.large;
  },

  hasCaption() {
    return settings.caption || settings.source;
  },
});

let definition = {
  tagName: 'article-figure',
  template,
  defaultSettings,
  createComponent,
};

definition = await TailwindPlugin(definition);

export const ArticleFigure = defineComponent(definition);
