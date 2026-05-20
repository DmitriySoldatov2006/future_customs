export const DEFAULT_FILTERS = Object.freeze({
  sort: 'default',
  partType: '',
  brand: '',
  carBrand: '',
  carModel: '',
  carGeneration: '',
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
      || merged.carBrand
      || merged.carModel
      || merged.carGeneration
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
    if (!matchesCompatibleVehicle(product, merged)) return false;
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

export function collectUniqueCarBrands(products) {
  const options = new Map();
  products.forEach((product) => {
    getProductCompatibleVehicles(product).forEach((vehicle) => {
      const value = String(vehicle.car_brand_id ?? '').trim();
      const label = String(vehicle.car_brand_name ?? '').trim();
      if (!value || !label || options.has(value)) return;
      options.set(value, label);
    });
  });
  return [...options.entries()]
    .map(([value, label]) => ({ value, label }))
    .sort((a, b) => compareText(a.label, b.label));
}

export function collectUniqueCarModels(products, carBrand = '') {
  const options = new Map();
  products
    .forEach((product) => {
      getProductCompatibleVehicles(product)
        .filter((vehicle) => !carBrand || String(vehicle.car_brand_id ?? '') === String(carBrand))
        .forEach((vehicle) => {
          const value = String(vehicle.car_model_id ?? '').trim();
          const label = String(vehicle.car_model_name ?? '').trim();
          if (!value || !label || options.has(value)) return;
          options.set(value, label);
        });
    });
  return [...options.entries()]
    .map(([value, label]) => ({ value, label }))
    .sort((a, b) => compareText(a.label, b.label));
}

export function collectUniqueCarGenerations(products, carBrand = '', carModel = '') {
  const options = new Map();
  products
    .forEach((product) => {
      getProductCompatibleVehicles(product)
        .filter((vehicle) => !carBrand || String(vehicle.car_brand_id ?? '') === String(carBrand))
        .filter((vehicle) => !carModel || String(vehicle.car_model_id ?? '') === String(carModel))
        .forEach((vehicle) => {
          const value = String(vehicle.car_generation_id ?? '').trim();
          const label = String(vehicle.car_generation_name ?? '').trim();
          if (!value || !label || options.has(value)) return;
          options.set(value, label);
        });
    });
  return [...options.entries()]
    .map(([value, label]) => ({ value, label }))
    .sort((a, b) => compareText(a.label, b.label));
}

export function collectPartTypeCharacteristics(products, partType) {
  if (!partType) return [];

  const byKey = new Map();
  products
    .filter((product) => getProductPartType(product) === partType)
    .forEach((product) => {
      Object.entries(product.characteristics || {}).forEach(([key, rawCharacteristic]) => {
        const characteristic = normalizeCharacteristic(rawCharacteristic);
        const values = extractCharacteristicValues(rawCharacteristic);
        if (!values.length) return;
        if (!byKey.has(key)) {
          byKey.set(key, {
            key,
            label: characteristic.label || key,
            values: new Set(),
          });
        }
        values.forEach((value) => {
          byKey.get(key).values.add(value);
        });
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

function getProductCompatibleVehicles(product) {
  const compatibleVehicles = Array.isArray(product.compatible_vehicles)
    ? product.compatible_vehicles
        .filter(Boolean)
        .map((vehicle) => ({
          car_brand_id: String(vehicle.car_brand_id ?? '').trim(),
          car_brand_name: String(vehicle.car_brand_name ?? '').trim(),
          car_model_id: String(vehicle.car_model_id ?? '').trim(),
          car_model_name: String(vehicle.car_model_name ?? '').trim(),
          car_generation_id: String(vehicle.car_generation_id ?? '').trim(),
          car_generation_name: String(vehicle.car_generation_name ?? '').trim(),
        }))
        .filter((vehicle) => vehicle.car_brand_id)
    : [];
  if (compatibleVehicles.length) {
    return compatibleVehicles;
  }
  const legacyVehicle = {
    car_brand_id: String(product.car_brand_id ?? '').trim(),
    car_brand_name: String(product.car_brand_name ?? '').trim(),
    car_model_id: String(product.car_model_id ?? '').trim(),
    car_model_name: String(product.car_model_name ?? '').trim(),
    car_generation_id: String(product.car_generation_id ?? '').trim(),
    car_generation_name: String(product.car_generation_name ?? '').trim(),
  };
  return legacyVehicle.car_brand_id ? [legacyVehicle] : [];
}

function matchesCompatibleVehicle(product, filters) {
  const vehicles = getProductCompatibleVehicles(product);
  if (!filters.carBrand && !filters.carModel && !filters.carGeneration) {
    return true;
  }
  return vehicles.some((vehicle) => {
    if (filters.carBrand && vehicle.car_brand_id !== String(filters.carBrand)) return false;
    if (filters.carModel && vehicle.car_model_id !== String(filters.carModel)) return false;
    if (filters.carGeneration && vehicle.car_generation_id !== String(filters.carGeneration)) return false;
    return true;
  });
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

    const productValues = extractCharacteristicValues(product.characteristics?.[key]);
    if (!productValues.length) return false;

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

function extractCharacteristicValues(rawCharacteristic) {
  const characteristic = normalizeCharacteristic(rawCharacteristic);
  if (Array.isArray(characteristic.value)) {
    return characteristic.value.map((value) => String(value)).filter(Boolean);
  }
  return [String(characteristic.value ?? '')].filter(Boolean);
}
