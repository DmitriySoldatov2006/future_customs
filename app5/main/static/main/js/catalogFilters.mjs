export const DEFAULT_FILTERS = Object.freeze({
  sort: 'default',
  partType: '',
  brand: '',
  minPrice: '',
  maxPrice: '',
  characteristics: {},
});

const sorters = {
  default: null,
  name_asc: (a, b) => compareText(a.name, b.name),
  name_desc: (a, b) => compareText(b.name, a.name),
  price_asc: (a, b) => getProductPrice(a) - getProductPrice(b),
  price_desc: (a, b) => getProductPrice(b) - getProductPrice(a),
};

const textCollator = new Intl.Collator('ru', {
  sensitivity: 'base',
  numeric: true,
});

export function normalizeText(value) {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase('ru')
    .trim();
}

export function getProductPrice(product) {
  const normalized = String(product?.price ?? '0')
    .replace(/\s/g, '')
    .replace(',', '.')
    .replace(/[^\d.-]/g, '');
  const value = Number(normalized);
  return Number.isFinite(value) ? value : 0;
}

export function sanitizePriceInput(value) {
  return String(value ?? '').replace(/[^\d]/g, '');
}

export function isPriceRangeInvalid(filters = {}) {
  const minPrice = parseOptionalPrice(filters.minPrice);
  const maxPrice = parseOptionalPrice(filters.maxPrice);
  return minPrice !== null && maxPrice !== null && minPrice > maxPrice;
}

export function hasActiveCriteria({ query = '', filters = {} } = {}) {
  const merged = mergeFilters(filters);
  return Boolean(
    normalizeText(query)
      || merged.partType
      || merged.brand
      || merged.minPrice
      || merged.maxPrice
      || merged.sort !== 'default'
      || Object.values(merged.characteristics).some((values) => values.length > 0),
  );
}

export function filterProducts(products, { query = '', filters = {} } = {}) {
  const merged = mergeFilters(filters);
  const normalizedQuery = normalizeText(query);
  const minPrice = parseOptionalPrice(merged.minPrice);
  const maxPrice = parseOptionalPrice(merged.maxPrice);
  const shouldApplyPrice = !isPriceRangeInvalid(merged);

  const filtered = products.filter((product) => {
    if (normalizedQuery && !matchesQuery(product, normalizedQuery)) return false;
    if (merged.partType && getProductPartType(product) !== merged.partType) return false;
    if (merged.brand && String(product.brand ?? '') !== merged.brand) return false;
    if (!matchesCharacteristics(product, merged.characteristics)) return false;

    if (shouldApplyPrice) {
      const price = getProductPrice(product);
      if (minPrice !== null && price < minPrice) return false;
      if (maxPrice !== null && price > maxPrice) return false;
    }

    return true;
  });

  const sorter = sorters[merged.sort] || null;
  return sorter ? [...filtered].sort(sorter) : filtered;
}

export function collectUniquePartTypes(products) {
  const options = new Map();
  products.forEach((product) => {
    const value = getProductPartType(product);
    if (!value || options.has(value)) return;
    options.set(value, product.part_type_label || product.category_name || value);
  });
  return [...options.entries()]
    .map(([value, label]) => ({ value, label }))
    .sort((a, b) => compareText(a.label, b.label));
}

export function collectUniqueBrands(products) {
  return [...new Set(products.map((product) => String(product.brand ?? '').trim()).filter(Boolean))]
    .sort(compareText)
    .map((brand) => ({ value: brand, label: brand }));
}

export function collectBrandCharacteristics(products, brand) {
  if (!brand) return [];

  const byKey = new Map();
  products
    .filter((product) => String(product.brand ?? '') === brand)
    .forEach((product) => {
      Object.entries(product.characteristics || {}).forEach(([key, rawCharacteristic]) => {
        const characteristic = normalizeCharacteristic(rawCharacteristic);
        if (!characteristic.value) return;
        if (!byKey.has(key)) {
          byKey.set(key, {
            key,
            label: characteristic.label || key,
            values: new Set(),
          });
        }
        byKey.get(key).values.add(characteristic.value);
      });
    });

  return [...byKey.values()]
    .map((item) => ({
      key: item.key,
      label: item.label,
      values: [...item.values].sort(compareText),
    }))
    .filter((item) => item.values.length > 0)
    .sort((a, b) => compareText(a.label, b.label));
}

function mergeFilters(filters) {
  return {
    ...DEFAULT_FILTERS,
    ...filters,
    characteristics: normalizeSelectedCharacteristics(filters.characteristics || {}),
  };
}

function normalizeSelectedCharacteristics(characteristics) {
  return Object.fromEntries(
    Object.entries(characteristics).map(([key, values]) => [
      key,
      Array.isArray(values)
        ? values.map((value) => String(value)).filter(Boolean)
        : [String(values)].filter(Boolean),
    ]),
  );
}

function compareText(a, b) {
  return textCollator.compare(String(a ?? ''), String(b ?? ''));
}

function parseOptionalPrice(value) {
  const sanitized = sanitizePriceInput(value);
  if (!sanitized) return null;
  const parsed = Number(sanitized);
  return Number.isFinite(parsed) ? parsed : null;
}

function getProductPartType(product) {
  return String(product.part_type || product.category_slug || product.category_name || '');
}

function matchesQuery(product, normalizedQuery) {
  return [
    product.name,
    product.article,
    product.vin_number,
    product.part_number,
    product.brand,
  ].some((value) => normalizeText(value).includes(normalizedQuery));
}

function matchesCharacteristics(product, selectedCharacteristics) {
  return Object.entries(selectedCharacteristics).every(([key, selectedValues]) => {
    if (!selectedValues.length) return true;

    const characteristic = normalizeCharacteristic(product.characteristics?.[key]);
    if (!characteristic.value) return false;

    const productValues = Array.isArray(characteristic.value)
      ? characteristic.value.map(String)
      : [String(characteristic.value)];

    return selectedValues.every((selectedValue) => productValues.includes(String(selectedValue)));
  });
}

function normalizeCharacteristic(rawCharacteristic) {
  if (rawCharacteristic && typeof rawCharacteristic === 'object' && !Array.isArray(rawCharacteristic)) {
    return {
      label: String(rawCharacteristic.label || ''),
      value: rawCharacteristic.value,
    };
  }
  return {
    label: '',
    value: rawCharacteristic,
  };
}
