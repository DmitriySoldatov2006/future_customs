import assert from 'node:assert/strict';

import {
  DEFAULT_FILTERS,
  filterProducts,
  isPriceRangeInvalid,
} from '../app5/main/static/main/js/catalogFilters.mjs';

const products = [
  {
    id: '1',
    name: 'Brembo Prime Brake Pads',
    article: 'BRK-500',
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
    name: 'ATE Brake Disc',
    article: 'DISC-1000',
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
    name: 'Bosch Cabin Filter',
    article: 'FLT-1500',
    brand: 'Bosch',
    category_slug: 'filters',
    part_type: 'filters',
    part_type_label: 'Фильтры',
    price: '1500',
    characteristics: {
      size: { label: 'Размер', value: 'M' },
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

assert.equal(filterProducts(products, defaultState).length, products.length, 'empty query returns all products');

assert.deepEqual(
  ids(filterProducts(products, { query: 'brake', filters: defaultState.filters })),
  ['1', '2'],
  'query matches name/article/brand case-insensitively',
);

assert.deepEqual(
  ids(filterProducts(products, { query: '', filters: { ...defaultState.filters, minPrice: '500' } })),
  ['1', '2', '4'],
  'minPrice excludes products priced below 500',
);

assert.deepEqual(
  ids(filterProducts(products, { query: '', filters: { ...defaultState.filters, maxPrice: '1000' } })),
  ['1', '2', '3'],
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
  ['2', '4', '1', '3'],
  'name_asc sorts A to Z',
);

assert.deepEqual(
  ids(filterProducts(products, { query: '', filters: { ...defaultState.filters, sort: 'name_desc' } })),
  ['3', '1', '4', '2'],
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
  ids(filterProducts(products, { query: 'brake', filters: { ...defaultState.filters, brand: 'ATE' } })),
  ['2'],
  'search and brand filter use AND logic',
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
