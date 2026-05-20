import assert from 'node:assert/strict';

import {
  DEFAULT_FILTERS,
  filterProducts,
  isPriceRangeInvalid,
} from '../app5/main/static/main/js/catalogFilters.js';

const products = [
  {
    id: '1',
    name: 'Brembo Prime Brake Pads',
    article: 'BRK-500',
    part_number: 'PAD-500',
    brand: 'Brembo',
    category_slug: 'brakes',
    part_type: 'brakes',
    part_type_label: 'Тормоза',
    price: '500',
    characteristics: {
      material: { label: 'Материал', value: 'Керамика' },
    },
  },
  {
    id: '2',
    name: 'ATE Disc Kit',
    article: 'BRAKE-1000',
    part_number: 'DISC-1000',
    brand: 'ATE',
    category_slug: 'brakes',
    part_type: 'brakes',
    part_type_label: 'Тормоза',
    price: '1000',
    characteristics: {
      material: { label: 'Материал', value: 'Металл' },
    },
  },
  {
    id: '3',
    name: 'KYB Shock Absorber',
    article: 'SUS-450',
    part_number: 'SUS-450',
    brand: 'KYB',
    category_slug: 'suspension',
    part_type: 'suspension',
    part_type_label: 'Подвеска',
    price: '450',
    characteristics: {
      axis: { label: 'Ось', value: 'Передняя' },
    },
  },
  {
    id: '4',
    name: 'Cabin Filter',
    article: 'FLT-1500',
    part_number: 'FLT-1500',
    brand: 'BrakePro',
    category_slug: 'filters',
    part_type: 'filters',
    part_type_label: 'Фильтры',
    price: '1500',
    characteristics: {
      size: { label: 'Размер', value: 'M' },
    },
  },
  {
    id: '5',
    name: 'Sensor Cafe',
    article: 'SNS-700',
    part_number: 'SNS-700',
    brand: 'Café Parts',
    category_slug: 'sensors',
    part_type: 'sensors',
    part_type_label: 'Датчики',
    price: '700',
    characteristics: {
      line: { label: 'Линейка', value: 'Premium' },
    },
  },
];

const defaultState = {
  query: '',
  filters: {
    ...DEFAULT_FILTERS,
    characteristics: {},
  },
};

const ids = (items) => items.map((item) => item.id);

assert.equal(
  filterProducts(products, defaultState).length,
  products.length,
  'empty query returns all products',
);

assert.deepEqual(
  ids(filterProducts(products, { query: 'brake', filters: defaultState.filters })),
  ['1', '2', '4'],
  'query matches name/article/brand case-insensitively',
);

assert.deepEqual(
  ids(filterProducts(products, { query: 'cafe', filters: defaultState.filters })),
  ['5'],
  'query matching is accent-insensitive',
);

assert.deepEqual(
  ids(filterProducts(products, { query: '', filters: { ...defaultState.filters, minPrice: '500' } })),
  ['1', '2', '4', '5'],
  'minPrice excludes products priced below 500',
);

assert.deepEqual(
  ids(filterProducts(products, { query: '', filters: { ...defaultState.filters, maxPrice: '1000' } })),
  ['1', '2', '3', '5'],
  'maxPrice excludes products priced above 1000',
);

const invalidPriceFilters = { ...defaultState.filters, minPrice: '1200', maxPrice: '800' };
assert.equal(isPriceRangeInvalid(invalidPriceFilters), true, 'min > max is invalid');
assert.deepEqual(
  ids(filterProducts(products, { query: '', filters: invalidPriceFilters })),
  ids(products),
  'invalid price range does not filter products',
);

assert.equal(
  filterProducts(products, { query: '', filters: { ...defaultState.filters, sort: 'price_asc' } })[0].id,
  '3',
  'price_asc puts lowest price first',
);

assert.equal(
  filterProducts(products, { query: '', filters: { ...defaultState.filters, sort: 'price_desc' } })[0].id,
  '4',
  'price_desc puts highest price first',
);

assert.deepEqual(
  ids(filterProducts(products, { query: '', filters: { ...defaultState.filters, sort: 'name_asc' } })),
  ['2', '1', '4', '3', '5'],
  'name_asc sorts A to Z',
);

assert.deepEqual(
  ids(filterProducts(products, { query: '', filters: { ...defaultState.filters, sort: 'name_desc' } })),
  ['5', '3', '4', '1', '2'],
  'name_desc sorts Z to A',
);

assert.deepEqual(
  ids(filterProducts(products, { query: '', filters: { ...defaultState.filters, brand: 'Brembo' } })),
  ['1'],
  'brand filter returns only selected brand',
);

assert.deepEqual(
  ids(filterProducts(products, { query: '', filters: { ...defaultState.filters, partType: 'brakes' } })),
  ['1', '2'],
  'part type filter returns only selected type',
);

assert.deepEqual(
  ids(filterProducts(products, { query: 'brake', filters: { ...defaultState.filters, brand: 'BrakePro' } })),
  ['4'],
  'search and brand filter use AND logic',
);

assert.deepEqual(
  ids(
    filterProducts(products, {
      query: '',
      filters: {
        ...defaultState.filters,
        partType: 'brakes',
        characteristics: {
          material: ['Керамика'],
        },
      },
    }),
  ),
  ['1'],
  'dynamic characteristic filters narrow the selected part type result set',
);

assert.equal(
  filterProducts(products, {
    query: '',
    filters: {
      ...DEFAULT_FILTERS,
      characteristics: {},
    },
  }).length,
  products.length,
  'reset state restores full product list',
);

console.log('catalog-filter-tests: all assertions passed');
