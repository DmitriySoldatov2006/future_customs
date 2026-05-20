(function () {
  const navShell = document.querySelector('[data-admin-nav]');
  if (!navShell) return;

  const brandsDataNode = document.getElementById('admin-panel-brands-data');
  const partTypesDataNode = document.getElementById('admin-panel-part-types-data');
  const carBrandsDataNode = document.getElementById('admin-panel-car-brands-data');
  const productsSearchInput = document.querySelector('[data-admin-products-search]');
  const partTypesSearchInput = document.querySelector('[data-admin-part-types-search]');
  const brandsSearchInput = document.querySelector('[data-admin-brands-search]');
  const carsSearchInput = document.querySelector('[data-admin-cars-search]');
  const usersSearchInput = document.querySelector('[data-admin-users-search]');

  const state = {
    brands: safeParseJson(brandsDataNode?.textContent, []),
    partTypes: safeParseJson(partTypesDataNode?.textContent, []),
    carBrands: safeParseJson(carBrandsDataNode?.textContent, []),
    currentSection: 'create-product',
    manage: {
      products: [],
      partTypes: [],
      brands: [],
      cars: [],
      users: [],
    },
    manageSearch: {
      products: '',
      partTypes: '',
      brands: '',
      cars: '',
      users: '',
    },
  };

  const sections = [...document.querySelectorAll('[data-admin-section]')];
  const tabs = [...document.querySelectorAll('[data-admin-tab]')];
  const navToggleButton = document.querySelector('[data-admin-nav-toggle]');

  const productForm = document.querySelector('[data-product-form]');
  const productBrandSelect = document.querySelector('[data-product-brand-select]');
  const productCompatibleVehicles = document.querySelector('[data-product-compatible-vehicles]');
  const productPartTypeSelect = document.querySelector('[data-product-part-type-select]');
  const productCharacteristicsSection = document.querySelector('[data-product-characteristics-section]');
  const productCharacteristicsFields = document.querySelector('[data-product-characteristics-fields]');
  const productImagesInput = document.querySelector('[data-product-images-input]');
  const productImagesTrigger = document.querySelector('[data-product-images-trigger]');
  const productImagesList = document.querySelector('[data-product-images-list]');

  const partTypeForm = document.querySelector('[data-part-type-form]');
  const characteristicGroups = document.querySelector('[data-characteristic-groups]');
  const addCharacteristicGroupButton = document.querySelector('[data-add-characteristic-group]');

  const brandForm = document.querySelector('[data-brand-form]');
  const carBrandForm = document.querySelector('[data-car-brand-form]');
  const carBrandInput = document.querySelector('[data-car-brand-input]');
  const carBrandSubmit = document.querySelector('[data-car-brand-submit]');
  const carModelForm = document.querySelector('[data-car-model-form]');
  const carModelBrandSelect = document.querySelector('[data-car-model-brand-select]');
  const carModelInput = document.querySelector('[data-car-model-input]');
  const carModelSubmit = document.querySelector('[data-car-model-submit]');
  const carGenerationForm = document.querySelector('[data-car-generation-form]');
  const carGenerationBrandSelect = document.querySelector('[data-car-generation-brand-select]');
  const carGenerationModelField = document.querySelector('[data-car-generation-model-field]');
  const carGenerationModelSelect = document.querySelector('[data-car-generation-model-select]');
  const carGenerationInput = document.querySelector('[data-car-generation-input]');
  const carGenerationSubmit = document.querySelector('[data-car-generation-submit]');

  const sectionNodes = {
    products: {
      status: document.querySelector('[data-admin-products-status]'),
      list: document.querySelector('[data-admin-products-list]'),
    },
    partTypes: {
      status: document.querySelector('[data-admin-part-types-status]'),
      list: document.querySelector('[data-admin-part-types-list]'),
    },
    brands: {
      status: document.querySelector('[data-admin-brands-status]'),
      list: document.querySelector('[data-admin-brands-list]'),
    },
    cars: {
      status: document.querySelector('[data-admin-cars-status]'),
      list: document.querySelector('[data-admin-cars-list]'),
    },
    users: {
      status: document.querySelector('[data-admin-users-status]'),
      list: document.querySelector('[data-admin-users-list]'),
    },
  };

  const feedbackNode = document.querySelector('[data-admin-feedback]');
  const modalNode = document.querySelector('[data-admin-modal]');
  const modalTextNode = document.querySelector('[data-admin-modal-text]');
  const modalConfirmButton = document.querySelector('[data-admin-modal-confirm]');
  const modalCloseButtons = [...document.querySelectorAll('[data-admin-modal-close]')];

  const endpoints = {
    brands: navShell.dataset.brandsEndpoint,
    partTypes: navShell.dataset.partTypesEndpoint,
    products: navShell.dataset.productsEndpoint,
    users: navShell.dataset.usersEndpoint,
    carBrands: navShell.dataset.carBrandsEndpoint,
    carModels: navShell.dataset.carModelsEndpoint,
    carGenerations: navShell.dataset.carGenerationsEndpoint,
  };

  const selectedProductImages = [];
  let productCompatibleVehiclesDraft = [];
  let feedbackTimer = null;
  let modalAction = null;

  function safeParseJson(value, fallback) {
    try {
      return JSON.parse(value || 'null') ?? fallback;
    } catch (error) {
      return fallback;
    }
  }

  function getCookie(name) {
    const match = document.cookie
      .split(';')
      .map((item) => item.trim())
      .find((item) => item.startsWith(`${name}=`));
    return match ? decodeURIComponent(match.split('=').slice(1).join('=')) : '';
  }

  function syncStickyOffset() {
    const header = document.querySelector('header');
    const headerOffset = header ? header.offsetHeight : 72;
    document.documentElement.style.setProperty('--admin-panel-sticky-top', `${headerOffset + 14}px`);
  }

  function buildItemEndpoint(base, id, action) {
    return `${base}${id}/${action}/`;
  }

  function isMobileAdminNav() {
    return window.matchMedia('(max-width: 768px)').matches;
  }

  function setAdminNavOpen(isOpen) {
    navShell.classList.toggle('is-open', isOpen);
    navToggleButton?.setAttribute('aria-expanded', String(isOpen));
  }

  function showNotice(message, type = 'success') {
    if (!feedbackNode) return;
    feedbackNode.hidden = false;
    feedbackNode.textContent = message;
    feedbackNode.classList.toggle('is-error', type === 'error');
    feedbackNode.classList.toggle('is-success', type !== 'error');
    window.clearTimeout(feedbackTimer);
    feedbackTimer = window.setTimeout(() => {
      feedbackNode.hidden = true;
    }, 3600);
  }

  function normalizeAdminSearch(value) {
    return String(value || '').trim().toLocaleLowerCase('ru');
  }

  function matchesAdminName(value, query) {
    if (!query) return true;
    return normalizeAdminSearch(value).includes(query);
  }

  function openModal(message, action) {
    if (!modalNode || !modalTextNode) return;
    modalAction = action;
    modalTextNode.textContent = message;
    modalNode.hidden = false;
  }

  function closeModal() {
    if (!modalNode) return;
    modalNode.hidden = true;
    modalAction = null;
    if (modalConfirmButton) modalConfirmButton.disabled = false;
  }

  async function confirmModalAction() {
    if (!modalAction || !modalConfirmButton) return;
    modalConfirmButton.disabled = true;
    try {
      await modalAction();
      closeModal();
    } catch (error) {
      modalConfirmButton.disabled = false;
      showNotice(error.message || 'Не удалось выполнить действие.', 'error');
    }
  }

  function switchSection(target) {
    state.currentSection = target;
    if (isMobileAdminNav()) {
      setAdminNavOpen(false);
    }
    tabs.forEach((tab) => {
      tab.classList.toggle('is-active', tab.dataset.adminTab === target);
    });
    sections.forEach((section) => {
      const isActive = section.dataset.adminSection === target;
      section.hidden = !isActive;
      section.classList.toggle('is-active', isActive);
    });

    if (target === 'products') loadProductsSection();
    if (target === 'part-types') loadPartTypesSection();
    if (target === 'brands') loadBrandsSection();
    if (target === 'cars') loadCarsSection();
    if (target === 'users') loadUsersSection();
  }

  function fillSelect(select, items, defaultLabel) {
    if (!select) return;
    const previousValue = select.value;
    select.replaceChildren();

    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = defaultLabel;
    select.append(defaultOption);

    items.forEach((item) => {
      const option = document.createElement('option');
      option.value = String(item.id);
      option.textContent = item.name;
      select.append(option);
    });

    if (items.some((item) => String(item.id) === previousValue)) {
      select.value = previousValue;
    }
  }

  function renderProductSelects() {
    fillSelect(productBrandSelect, state.brands, 'Выберите производителя');
    fillSelect(productPartTypeSelect, state.partTypes, 'Выберите катагорию');
  }

  function getCarBrandById(brandId) {
    return state.carBrands.find((item) => String(item.id) === String(brandId || ''));
  }

  function getCarModelById(brandId, modelId) {
    const brand = getCarBrandById(brandId);
    if (!brand) return null;
    return (brand.models || []).find((item) => String(item.id) === String(modelId || ''));
  }

  function createEmptyCompatibleVehicle() {
    return {
      car_brand_id: '',
      car_model_id: '',
      car_generation_id: '',
    };
  }

  function normalizeCompatibleVehiclesDraft(items) {
    const normalized = Array.isArray(items)
      ? items.map((item) => ({
          car_brand_id: String(item?.car_brand_id || ''),
          car_model_id: String(item?.car_model_id || ''),
          car_generation_id: String(item?.car_generation_id || ''),
        }))
      : [];
    return normalized.length ? normalized : [createEmptyCompatibleVehicle()];
  }

  function createCompatibleVehicleSelect(labelText, items, selectedValue, defaultLabel, onChange, options = {}) {
    const field = createFieldWrapper(labelText);
    const row = document.createElement('div');
    row.className = 'select-row';
    const select = document.createElement('select');
    if (options.disabled) {
      select.disabled = true;
    }

    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = defaultLabel;
    select.append(defaultOption);

    items.forEach((item) => {
      const option = document.createElement('option');
      option.value = String(item.id);
      option.textContent = item.name;
      select.append(option);
    });

    select.value = selectedValue ? String(selectedValue) : '';
    select.addEventListener('change', () => onChange(select.value));
    row.append(select);
    field.append(row);
    return field;
  }

  function createCompatibleVehicleRow(vehicle, index, total, handlers) {
    const row = document.createElement('div');
    row.className = 'admin-compatible-vehicle-row';

    const brand = getCarBrandById(vehicle.car_brand_id);
    const models = (brand?.models || []).map((model) => ({ id: model.id, name: model.name }));
    const generations = (getCarModelById(vehicle.car_brand_id, vehicle.car_model_id)?.generations || []).map((generation) => ({
      id: generation.id,
      name: generation.name,
    }));

    row.append(
      createCompatibleVehicleSelect('Марка авто', state.carBrands, vehicle.car_brand_id, 'Выберите марку', handlers.onBrandChange),
      createCompatibleVehicleSelect('Модель авто', models, vehicle.car_model_id, 'Выберите модель', handlers.onModelChange, {
        disabled: !vehicle.car_brand_id,
      }),
      createCompatibleVehicleSelect('Поколение авто', generations, vehicle.car_generation_id, 'Выберите поколение', handlers.onGenerationChange, {
        disabled: !vehicle.car_model_id,
      }),
    );

    const actions = document.createElement('div');
    actions.className = 'admin-form-field admin-compatible-vehicle-actions';

    const spacer = document.createElement('span');
    spacer.className = 'admin-compatible-vehicle-actions__spacer';
    spacer.textContent = 'Действия';

    const actionsStack = document.createElement('div');
    actionsStack.className = 'admin-compatible-vehicle-actions__stack';

    const addButton = document.createElement('button');
    addButton.type = 'button';
    addButton.className = 'admin-inline-add';
    addButton.classList.toggle('is-hidden', index !== total - 1);
    addButton.innerHTML = '<span class="admin-inline-add__icon" aria-hidden="true"></span>';
    addButton.addEventListener('click', handlers.onAdd);

    const removeButton = document.createElement('button');
    removeButton.type = 'button';
    removeButton.className = 'admin-inline-remove';
    removeButton.classList.toggle('is-hidden', total <= 1 || index === total - 1);
    removeButton.innerHTML = '<span class="admin-inline-add__icon admin-inline-add__icon--remove" aria-hidden="true"></span>';
    removeButton.addEventListener('click', handlers.onRemove);

    actionsStack.append(addButton, removeButton);
    actions.append(spacer, actionsStack);
    row.append(actions);
    return row;
  }

  function renderProductCompatibleVehicles() {
    if (!productCompatibleVehicles) return;
    productCompatibleVehiclesDraft = normalizeCompatibleVehiclesDraft(productCompatibleVehiclesDraft);
    productCompatibleVehicles.replaceChildren();

    productCompatibleVehiclesDraft.forEach((vehicle, index) => {
      productCompatibleVehicles.append(
        createCompatibleVehicleRow(vehicle, index, productCompatibleVehiclesDraft.length, {
          onBrandChange: (value) => {
            vehicle.car_brand_id = value;
            vehicle.car_model_id = '';
            vehicle.car_generation_id = '';
            renderProductCompatibleVehicles();
          },
          onModelChange: (value) => {
            vehicle.car_model_id = value;
            vehicle.car_generation_id = '';
            renderProductCompatibleVehicles();
          },
          onGenerationChange: (value) => {
            vehicle.car_generation_id = value;
          },
          onAdd: () => {
            productCompatibleVehiclesDraft.push(createEmptyCompatibleVehicle());
            renderProductCompatibleVehicles();
          },
          onRemove: () => {
            productCompatibleVehiclesDraft.splice(index, 1);
            renderProductCompatibleVehicles();
          },
        }),
      );
    });
  }

  function renderCarBrandSelect() {
    fillSelect(carModelBrandSelect, state.carBrands, 'Выберите марку автомобиля');
  }

  function renderCarGenerationBrandSelect() {
    fillSelect(carGenerationBrandSelect, state.carBrands, 'Выберите марку автомобиля');
  }

  function renderCarGenerationModelSelect() {
    if (!carGenerationModelField || !carGenerationModelSelect) return;

    const selectedBrand = getCarBrandById(carGenerationBrandSelect?.value || '');
    carGenerationModelSelect.replaceChildren();

    if (!selectedBrand) {
      carGenerationModelSelect.disabled = true;
      carGenerationModelSelect.value = '';
      carGenerationModelField.hidden = true;
      return;
    }

    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'Выберите модель автомобиля';
    carGenerationModelSelect.append(defaultOption);

    (selectedBrand.models || []).forEach((model) => {
      const option = document.createElement('option');
      option.value = String(model.id);
      option.textContent = model.name;
      carGenerationModelSelect.append(option);
    });

    carGenerationModelField.hidden = false;
    carGenerationModelSelect.disabled = !(selectedBrand.models || []).length;
  }

  function syncCarFormButtons() {
    if (carBrandSubmit) {
      carBrandSubmit.disabled = !(carBrandInput?.value.trim());
    }
    if (carModelSubmit) {
      carModelSubmit.disabled = !(carModelBrandSelect?.value && carModelInput?.value.trim());
    }
    if (carGenerationSubmit) {
      carGenerationSubmit.disabled = !(
        carGenerationBrandSelect?.value &&
        carGenerationModelSelect?.value &&
        carGenerationInput?.value.trim()
      );
    }
  }

  function getImageKey(file) {
    return [file.name, file.size, file.lastModified].join(':');
  }

  function formatFileSize(size) {
    if (!Number.isFinite(size) || size <= 0) return '0 Б';
    if (size < 1024) return `${size} Б`;
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} КБ`;
    return `${(size / (1024 * 1024)).toFixed(1)} МБ`;
  }

  function renderSelectedProductImages() {
    if (!productImagesList) return;
    productImagesList.replaceChildren();

    if (!selectedProductImages.length) {
      const emptyState = document.createElement('p');
      emptyState.className = 'admin-upload-empty';
      emptyState.textContent = 'Изображения пока не выбраны.';
      productImagesList.append(emptyState);
      return;
    }

    selectedProductImages.forEach((file, index) => {
      const item = document.createElement('div');
      item.className = 'admin-upload-item';

      const meta = document.createElement('div');
      meta.className = 'admin-upload-item__meta';

      const name = document.createElement('span');
      name.className = 'admin-upload-item__name';
      name.textContent = file.name;

      const size = document.createElement('span');
      size.className = 'admin-upload-item__size';
      size.textContent = formatFileSize(file.size);

      meta.append(name, size);

      const removeButton = document.createElement('button');
      removeButton.type = 'button';
      removeButton.className = 'admin-upload-remove';
      removeButton.textContent = 'Удалить';
      removeButton.addEventListener('click', () => {
        selectedProductImages.splice(index, 1);
        renderSelectedProductImages();
      });

      item.append(meta, removeButton);
      productImagesList.append(item);
    });
  }

  function addSelectedProductImages(files) {
    const existingKeys = new Set(selectedProductImages.map(getImageKey));
    [...files].forEach((file) => {
      const key = getImageKey(file);
      if (existingKeys.has(key)) return;
      existingKeys.add(key);
      selectedProductImages.push(file);
    });
    renderSelectedProductImages();
  }

  function clearSelectedProductImages() {
    selectedProductImages.splice(0, selectedProductImages.length);
    if (productImagesInput) {
      productImagesInput.value = '';
    }
    renderSelectedProductImages();
  }

  function cloneAdminProductImages(images) {
    return Array.isArray(images)
      ? images.map((image) => ({
          id: String(image?.id || ''),
          name: String(image?.name || ''),
          url: String(image?.url || ''),
          sort_order: Number(image?.sort_order || 0),
          is_primary: Boolean(image?.is_primary),
        }))
      : [];
  }

  const orderStatusOptions = [
    { id: 'new', name: 'Новый' },
    { id: 'processing', name: 'В обработке' },
    { id: 'completed', name: 'Завершён' },
    { id: 'cancelled', name: 'Отменён' },
  ];

  function createEmptyOrderItemDraft() {
    return {
      id: '',
      product_id: '',
      name: '',
      quantity: '1',
      price: '',
    };
  }

  function cloneAdminOrderItems(items) {
    const normalized = Array.isArray(items)
      ? items.map((item) => ({
          id: String(item?.id || ''),
          product_id: String(item?.product_id || ''),
          name: String(item?.name || ''),
          quantity: String(item?.quantity || '1'),
          price: String(item?.price || ''),
        }))
      : [];
    return normalized.length ? normalized : [createEmptyOrderItemDraft()];
  }

  function cloneAdminOrders(orders) {
    return Array.isArray(orders)
      ? orders.map((order) => ({
          id: String(order?.id || ''),
          full_name: String(order?.full_name || ''),
          phone: String(order?.phone || ''),
          region: String(order?.region || ''),
          city: String(order?.city || ''),
          address: String(order?.address || ''),
          total: String(order?.total || ''),
          status: String(order?.status || 'new'),
          created_at: String(order?.created_at || ''),
          created_at_display: String(order?.created_at_display || ''),
          items: cloneAdminOrderItems(order?.items),
        }))
      : [];
  }

  function replaceArrayContents(target, nextItems) {
    target.splice(0, target.length, ...nextItems);
  }

  function getOrderStatusLabel(status) {
    const match = orderStatusOptions.find((item) => item.id === status);
    return match ? match.name : status || '—';
  }

  function formatAdminOrderTotal(total) {
    const normalized = String(total || '').trim();
    return normalized ? `${normalized} ₽` : '—';
  }

  function formatAdminOrderItemsSummary(items) {
    const names = Array.isArray(items)
      ? items.map((item) => String(item?.name || '').trim()).filter(Boolean)
      : [];
    return names.length ? names.join(', ') : '—';
  }

  function addDraftProductImages(draft, files) {
    if (!draft) return;
    if (!Array.isArray(draft.new_images)) {
      draft.new_images = [];
    }
    const existingKeys = new Set(draft.new_images.map(getImageKey));
    [...files].forEach((file) => {
      const key = getImageKey(file);
      if (existingKeys.has(key)) return;
      existingKeys.add(key);
      draft.new_images.push(file);
    });
  }

  function createCharacteristicValueRow() {
    const row = document.createElement('div');
    row.className = 'admin-value-row';
    row.innerHTML = `
      <div class="admin-value-row__input">
        <input type="text" name="value" placeholder="Характеристика">
      </div>
      <div class="admin-inline-action-slot">
        <button class="admin-inline-add" type="button" aria-label="Добавить характеристику">+</button>
        <button class="admin-inline-remove" type="button" aria-label="Удалить характеристику">Удалить</button>
      </div>
      <label class="admin-checkbox">
        <input type="checkbox" name="is_custom">
        <span>Индивидуальное значение</span>
      </label>
    `;

    const input = row.querySelector('input[name="value"]');
    const checkbox = row.querySelector('input[name="is_custom"]');
    const checkboxLabel = row.querySelector('.admin-checkbox');
    const addButton = row.querySelector('.admin-inline-add');
    const removeButton = row.querySelector('.admin-inline-remove');
    const actionSlot = row.querySelector('.admin-inline-action-slot');
    const addIcon = document.createElement('span');
    addIcon.className = 'admin-inline-add__icon';
    addIcon.setAttribute('aria-hidden', 'true');
    const removeIcon = document.createElement('span');
    removeIcon.className = 'admin-inline-add__icon admin-inline-add__icon--remove';
    removeIcon.setAttribute('aria-hidden', 'true');

    addButton.textContent = '';
    addButton.append(addIcon);
    removeButton.textContent = '';
    removeButton.append(removeIcon);
    removeButton.hidden = true;

    checkbox.addEventListener('change', () => {
      if (checkbox.checked) {
        const group = row.parentElement;
        const rows = [...(group?.querySelectorAll('.admin-value-row') || [])];
        rows.forEach((groupRow) => {
          const groupInput = groupRow.querySelector('input[name="value"]');
          if (groupInput) {
            groupInput.value = '';
          }
        });
      }
      syncInlineAddButtons();
    });

    addButton.addEventListener('click', () => {
      row.parentElement?.append(createCharacteristicValueRow());
      syncInlineAddButtons();
    });

    removeButton.addEventListener('click', () => {
      row.remove();
      syncInlineAddButtons();
    });

    checkboxLabel.hidden = true;

    return row;
  }

  function syncInlineAddButtons() {
    document.querySelectorAll('[data-characteristic-values]').forEach((group) => {
      const rows = [...group.querySelectorAll('.admin-value-row')];
      const firstCheckbox = rows[0]?.querySelector('input[name="is_custom"]');
      const isGroupCustom = Boolean(firstCheckbox?.checked);
      rows.forEach((row, index) => {
        const input = row.querySelector('input[name="value"]');
        const addButton = row.querySelector('.admin-inline-add');
        const removeButton = row.querySelector('.admin-inline-remove');
        const actionSlot = row.querySelector('.admin-inline-action-slot');
        const checkboxLabel = row.querySelector('.admin-checkbox');
        const checkbox = row.querySelector('input[name="is_custom"]');
        if (!input || !addButton || !removeButton || !actionSlot || !checkboxLabel || !checkbox) return;
        const isLastRow = index === rows.length - 1;
        checkbox.checked = index === 0 ? isGroupCustom : false;
        checkboxLabel.hidden = index !== 0;
        input.disabled = isGroupCustom;
        const showAddButton = isLastRow && !isGroupCustom;
        const showRemoveButton = rows.length > 1 && !showAddButton;
        addButton.hidden = !showAddButton;
        removeButton.hidden = !showRemoveButton;
        actionSlot.hidden = !showAddButton && !showRemoveButton;
        addButton.classList.toggle('is-hidden', !showAddButton);
        removeButton.classList.toggle('is-hidden', !showRemoveButton);
        actionSlot.classList.toggle('is-hidden', !showAddButton && !showRemoveButton);
        row.classList.toggle('admin-value-row--stacked', !showAddButton && !showRemoveButton);
      });
    });
  }

  function createCharacteristicGroup() {
    const wrapper = document.createElement('div');
    wrapper.className = 'filter-card admin-characteristic-builder';
    wrapper.dataset.characteristicGroup = 'true';
    wrapper.innerHTML = `
      <div class="admin-characteristic-builder__actions">
        <button class="admin-mini-button" type="button" data-remove-characteristic-group hidden>Удалить характеристику</button>
      </div>
      <label class="admin-form-field admin-form-field--wide">
        <span>Название характеристики</span>
        <input type="text" name="characteristic_name" placeholder="Например, Материал">
      </label>
      <div class="admin-characteristic-values" data-characteristic-values></div>
    `;

    wrapper.querySelector('[data-remove-characteristic-group]')?.addEventListener('click', () => {
      wrapper.remove();
      syncCharacteristicGroupButtons();
      syncInlineAddButtons();
    });
    wrapper.querySelector('[data-characteristic-values]')?.append(createCharacteristicValueRow());
    return wrapper;
  }

  function syncCharacteristicGroupButtons() {
    const groups = [...(characteristicGroups?.querySelectorAll('[data-characteristic-group]') || [])];
    groups.forEach((group, index) => {
      const removeButton = group.querySelector('[data-remove-characteristic-group]');
      if (!removeButton) return;
      removeButton.hidden = !(groups.length > 1 && index > 0);
    });
  }

  function collectPartTypePayload() {
    return {
      name: partTypeForm?.querySelector('input[name="name"]')?.value.trim() || '',
      characteristics: [...(characteristicGroups?.querySelectorAll('[data-characteristic-group]') || [])]
        .map((group) => {
          const name = group.querySelector('input[name="characteristic_name"]')?.value.trim() || '';
          const rows = [...group.querySelectorAll('.admin-value-row')];
          const isCustom = Boolean(rows[0]?.querySelector('input[name="is_custom"]')?.checked);
          const values = isCustom
            ? [{ value: '', is_custom: true }]
            : rows.map((row) => ({
                value: row.querySelector('input[name="value"]')?.value.trim() || '',
                is_custom: false,
              }));
          return { name, values };
        })
        .filter((item) => item.name),
    };
  }

  function findPartType(categoryId) {
    return state.partTypes.find((item) => String(item.id) === String(categoryId || ''));
  }

  function normalizeCharacteristicsForPartType(categoryId, rawCharacteristics) {
    const selectedType = findPartType(categoryId);
    if (!selectedType || !selectedType.characteristics.length) {
      return {};
    }

    const normalized = {};
    selectedType.characteristics.forEach((characteristic) => {
      const value = String((rawCharacteristics || {})[characteristic.key] || '').trim();
      if (!value) return;
      if (characteristic.allows_custom_value || characteristic.values.includes(value)) {
        normalized[characteristic.key] = value;
      }
    });
    return normalized;
  }

  function renderCreateProductCharacteristics() {
    if (!productCharacteristicsFields || !productCharacteristicsSection) return;
    productCharacteristicsFields.replaceChildren();

    const selectedType = findPartType(productPartTypeSelect?.value || '');
    if (!selectedType || !selectedType.characteristics.length) {
      productCharacteristicsSection.hidden = true;
      return;
    }

    productCharacteristicsSection.hidden = false;
    selectedType.characteristics.forEach((characteristic) => {
      productCharacteristicsFields.append(
        createProductCharacteristicEditorRow(characteristic, {}, () => {}),
      );
    });
  }

  function collectProductPayload() {
    const characteristics = {};
    productCharacteristicsFields?.querySelectorAll('[data-product-characteristic-key]').forEach((field) => {
      const value = field.value.trim();
      if (value) {
        characteristics[field.dataset.productCharacteristicKey] = value;
      }
    });

    return {
      name: productForm?.querySelector('input[name="name"]')?.value.trim() || '',
      short_description: productForm?.querySelector('textarea[name="short_description"]')?.value.trim() || '',
      description: productForm?.querySelector('textarea[name="description"]')?.value.trim() || '',
      article: productForm?.querySelector('input[name="article"]')?.value.trim() || '',
      vin_number: productForm?.querySelector('input[name="vin_number"]')?.value.trim() || '',
      price: productForm?.querySelector('input[name="price"]')?.value.trim() || '',
      stock_quantity: productForm?.querySelector('input[name="stock_quantity"]')?.value.trim() || '',
      brand_id: productBrandSelect?.value || '',
      compatible_vehicles: productCompatibleVehiclesDraft
        .map((item) => ({
          car_brand_id: item.car_brand_id || '',
          car_model_id: item.car_model_id || '',
          car_generation_id: item.car_generation_id || '',
        }))
        .filter((item) => item.car_brand_id),
      category_id: productPartTypeSelect?.value || '',
      characteristics,
    };
  }

  function buildProductFormData() {
    const payload = collectProductPayload();
    const formData = new FormData();

    formData.append('name', payload.name);
    formData.append('short_description', payload.short_description);
    formData.append('description', payload.description);
    formData.append('article', payload.article);
    formData.append('vin_number', payload.vin_number);
    formData.append('price', payload.price);
    formData.append('stock_quantity', payload.stock_quantity);
    formData.append('brand_id', payload.brand_id);
    formData.append('compatible_vehicles', JSON.stringify(payload.compatible_vehicles));
    formData.append('category_id', payload.category_id);
    formData.append('characteristics', JSON.stringify(payload.characteristics));

    selectedProductImages.forEach((file) => {
      formData.append('images', file, file.name);
    });

    return formData;
  }

  function buildProductUpdateFormData(draft) {
    const formData = new FormData();

    formData.append('name', draft.name || '');
    formData.append('short_description', draft.short_description || '');
    formData.append('description', draft.description || '');
    formData.append('article', draft.article || '');
    formData.append('vin_number', draft.vin_number || '');
    formData.append('price', draft.price ?? '');
    formData.append('stock_quantity', draft.stock_quantity ?? '');
    formData.append('brand_id', draft.brand_id || '');
    formData.append(
      'compatible_vehicles',
      JSON.stringify(
        normalizeCompatibleVehiclesDraft(draft.compatible_vehicles).filter((item) => item.car_brand_id),
      ),
    );
    formData.append('category_id', draft.category_id || '');
    formData.append(
      'characteristics',
      JSON.stringify(normalizeCharacteristicsForPartType(draft.category_id, draft.characteristics)),
    );
    formData.append('remove_image_ids', JSON.stringify((draft.removed_image_ids || []).map(String)));

    (draft.new_images || []).forEach((file) => {
      formData.append('images', file, file.name);
    });

    return formData;
  }

  async function parseResponse(response) {
    const data = await response.json().catch(() => ({
      ok: false,
      error: 'Не удалось обработать ответ сервера.',
    }));
    if (!response.ok || data.ok === false) {
      throw new Error(data.error || 'Запрос не выполнен.');
    }
    return data;
  }

  async function getJson(url) {
    const response = await fetch(url, {
      headers: {
        'X-Requested-With': 'fetch',
      },
    });
    return parseResponse(response);
  }

  async function postJson(url, payload) {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify(payload),
    });
    return parseResponse(response);
  }

  async function postFormData(url, formData) {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: formData,
    });
    return parseResponse(response);
  }

  async function refreshBrandsReferenceData() {
    const response = await getJson(endpoints.brands);
    state.brands = response.brands || [];
    renderProductSelects();
  }

  async function refreshPartTypesReferenceData() {
    const response = await getJson(endpoints.partTypes);
    state.partTypes = response.part_types || [];
    renderProductSelects();
    renderCreateProductCharacteristics();
  }

  async function refreshCarBrandsReferenceData() {
    const response = await getJson(endpoints.carBrands);
    state.carBrands = response.car_brands || [];
    renderCarBrandSelect();
    renderCarGenerationBrandSelect();
    renderProductCompatibleVehicles();
    renderCarGenerationModelSelect();
    syncCarFormButtons();
  }

  function setSectionLoading(sectionKey, message) {
    const section = sectionNodes[sectionKey];
    if (!section) return;
    section.status.hidden = false;
    section.status.textContent = message;
    section.status.classList.remove('is-error');
    section.list.hidden = true;
    section.list.replaceChildren();
  }

  function setSectionError(sectionKey, message) {
    const section = sectionNodes[sectionKey];
    if (!section) return;
    section.status.hidden = false;
    section.status.textContent = message;
    section.status.classList.add('is-error');
    section.list.hidden = true;
    section.list.replaceChildren();
  }

  function showSectionList(sectionKey, hasItems) {
    const section = sectionNodes[sectionKey];
    if (!section) return;
    section.status.hidden = hasItems;
    if (!hasItems) {
      section.status.classList.remove('is-error');
    }
    section.list.hidden = !hasItems;
  }

  async function loadProductsSection() {
    setSectionLoading('products', 'Загрузка товаров...');
    try {
      const response = await getJson(endpoints.products);
      state.manage.products = (response.products || []).map((item) => ({
        ...item,
        isEditing: false,
        draft: null,
      }));
      renderProductsSection();
    } catch (error) {
      setSectionError('products', error.message);
      showNotice(error.message, 'error');
    }
  }

  async function loadPartTypesSection() {
    setSectionLoading('partTypes', 'Загрузка типов товара...');
    try {
      const response = await getJson(endpoints.partTypes);
      state.partTypes = response.part_types || [];
      state.manage.partTypes = state.partTypes.map((item) => ({
        ...item,
        isEditing: false,
        draft: null,
      }));
      renderPartTypesSection();
      renderProductSelects();
      renderCreateProductCharacteristics();
    } catch (error) {
      setSectionError('partTypes', error.message);
      showNotice(error.message, 'error');
    }
  }

  async function loadBrandsSection() {
    setSectionLoading('brands', 'Загрузка производителей...');
    try {
      const response = await getJson(endpoints.brands);
      state.brands = response.brands || [];
      state.manage.brands = state.brands.map((item) => ({
        ...item,
        isEditing: false,
        draft: null,
      }));
      renderBrandsSection();
      renderProductSelects();
    } catch (error) {
      setSectionError('brands', error.message);
      showNotice(error.message, 'error');
    }
  }

  async function loadCarsSection() {
    setSectionLoading('cars', 'Загрузка марок и моделей авто...');
    try {
      const response = await getJson(endpoints.carBrands);
      state.carBrands = response.car_brands || [];
      state.manage.cars = state.carBrands.map((brand) => ({
        ...brand,
        isEditing: false,
        draft: null,
        models: (brand.models || []).map((model) => ({
          ...model,
          isEditing: false,
          draft: null,
          generations: (model.generations || []).map((generation) => ({
            ...generation,
            isEditing: false,
            draft: null,
          })),
        })),
      }));
      renderCarsSection();
      renderCarBrandSelect();
      renderCarGenerationBrandSelect();
      renderProductCompatibleVehicles();
      renderCarGenerationModelSelect();
      syncCarFormButtons();
    } catch (error) {
      setSectionError('cars', error.message);
      showNotice(error.message, 'error');
    }
  }

  async function loadUsersSection() {
    setSectionLoading('users', 'Загрузка пользователей...');
    try {
      const response = await getJson(endpoints.users);
      state.manage.users = (response.users || []).map((item) => ({
        ...item,
        orders: cloneAdminOrders(item.orders),
        isEditing: false,
        draft: null,
      }));
      renderUsersSection();
    } catch (error) {
      setSectionError('users', error.message);
      showNotice(error.message, 'error');
    }
  }

  function createActionButton(label, className, onClick) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = className;
    button.textContent = label;
    button.addEventListener('click', onClick);
    return button;
  }

  function createRecordItem(label, value, wide = false) {
    const wrapper = document.createElement('div');
    wrapper.className = `admin-record-item${wide ? ' admin-record-item--wide' : ''}`;

    const labelNode = document.createElement('span');
    labelNode.className = 'admin-record-label';
    labelNode.textContent = label;

    const valueNode = document.createElement('div');
    valueNode.className = 'admin-record-value';
    valueNode.textContent = value || '—';

    wrapper.append(labelNode, valueNode);
    return wrapper;
  }

  function createFieldWrapper(labelText, wide = false) {
    const label = document.createElement('label');
    label.className = `admin-form-field${wide ? ' admin-form-field--wide' : ''}`;

    const title = document.createElement('span');
    title.textContent = labelText;
    label.append(title);
    return label;
  }

  function createInputField(labelText, value, options = {}) {
    const field = createFieldWrapper(labelText, Boolean(options.wide));
    const input = document.createElement('input');
    input.type = options.type || 'text';
    input.value = value || '';
    input.placeholder = options.placeholder || '';
    if (options.min !== undefined) input.min = String(options.min);
    if (options.step !== undefined) input.step = String(options.step);
    if (options.inputMode) input.inputMode = options.inputMode;
    input.addEventListener('input', () => options.onInput?.(input.value));
    field.append(input);
    return field;
  }

  function createTextareaField(labelText, value, options = {}) {
    const field = createFieldWrapper(labelText, true);
    const textarea = document.createElement('textarea');
    textarea.rows = options.rows || 4;
    textarea.value = value || '';
    textarea.addEventListener('input', () => options.onInput?.(textarea.value));
    field.append(textarea);
    return field;
  }

  function createSelectField(labelText, value, items, defaultLabel, onChange) {
    const field = createFieldWrapper(labelText);
    const row = document.createElement('div');
    row.className = 'select-row';
    const select = document.createElement('select');

    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = defaultLabel;
    select.append(defaultOption);

    items.forEach((item) => {
      const option = document.createElement('option');
      option.value = String(item.id);
      option.textContent = item.name;
      select.append(option);
    });

    select.value = value ? String(value) : '';
    select.addEventListener('change', () => onChange(select.value));
    row.append(select);
    field.append(row);
    return field;
  }

  function createRoleSelectField(labelText, value, onChange) {
    const field = createFieldWrapper(labelText);
    const row = document.createElement('div');
    row.className = 'select-row';
    const select = document.createElement('select');
    [
      { value: 'user', label: 'user' },
      { value: 'admin', label: 'admin' },
    ].forEach((item) => {
      const option = document.createElement('option');
      option.value = item.value;
      option.textContent = item.label;
      select.append(option);
    });
    select.value = value || 'user';
    select.addEventListener('change', () => onChange(select.value));
    row.append(select);
    field.append(row);
    return field;
  }

  function createProductCharacteristicEditorRow(characteristic, valuesSource, onValueChange) {
    const row = document.createElement('div');
    row.className = 'dynamic-row admin-dynamic-row';

    const label = document.createElement('span');
    label.textContent = characteristic.name;
    row.append(label);

    if (characteristic.allows_custom_value) {
      const field = document.createElement('label');
      field.className = 'admin-form-field admin-form-field--inline';
      const input = document.createElement('input');
      input.type = 'text';
      input.value = valuesSource[characteristic.key] || '';
      input.dataset.productCharacteristicKey = characteristic.key;
      input.placeholder = characteristic.name;
      input.addEventListener('input', () => onValueChange(characteristic.key, input.value));
      field.append(input);
      row.append(field);
      return row;
    }

    const selectLabel = document.createElement('label');
    selectLabel.className = 'select-row';
    const select = document.createElement('select');
    select.dataset.productCharacteristicKey = characteristic.key;

    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'Выберите значение';
    select.append(defaultOption);

    characteristic.values.forEach((value) => {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = value;
      select.append(option);
    });

    select.value = valuesSource[characteristic.key] || '';
    select.addEventListener('change', () => onValueChange(characteristic.key, select.value));
    selectLabel.append(select);
    row.append(selectLabel);
    return row;
  }

  function createProductCharacteristicsEditor(draft, rerender) {
    const panel = document.createElement('div');
    panel.className = 'filter-card filter-card--dynamic admin-characteristics-panel';

    const head = document.createElement('div');
    head.className = 'filter-card__head';
    const title = document.createElement('h3');
    title.textContent = 'Характеристики';
    head.append(title);
    panel.append(head);
    /*

    const fields = document.createElement('div');
    fields.className = 'admin-characteristics-fields';

    const selectedType = findPartType(draft.category_id);
    if (!selectedType || !selectedType.characteristics.length) {
      const empty = document.createElement('div');
      empty.className = 'admin-data-status';
      empty.textContent = 'У выбранной катагории нет характеристик.';
      panel.append(empty);
      return panel;
    }

    draft.characteristics = normalizeCharacteristicsForPartType(draft.category_id, draft.characteristics);

    selectedType.characteristics.forEach((characteristic) => {
      fields.append(
        createProductCharacteristicEditorRow(characteristic, draft.characteristics, (key, value) => {
          const normalized = String(value || '').trim();
          if (normalized) {
            draft.characteristics[key] = normalized;
          } else {
            delete draft.characteristics[key];
          }
        }),
      );
    });

    panel.append(fields);
    return panel;
  }

  function formatCompatibleVehicles(value, fallback = '—') {
    const items = Array.isArray(value) ? value.filter((item) => item?.label) : [];
    return items.length ? items.map((item) => item.label).join(', ') : fallback;
  }

  function createProductCompatibleVehiclesEditor(draft, rerender) {
    const panel = document.createElement('div');
    panel.className = 'filter-card filter-card--dynamic admin-vehicle-panel';

    const head = document.createElement('div');
    head.className = 'filter-card__head';
    const title = document.createElement('h3');
    title.textContent = 'Совместимые авто';
    head.append(title);
    panel.append(head);

    const count = document.createElement('div');
    count.className = 'admin-data-status';
    count.textContent = `Количество заказов: ${orders.length}`;
    section.append(count);
    return section;

    const count = document.createElement('div');
    count.className = 'admin-data-status';
    count.textContent = `Количество заказов: ${orders.length}`;
    section.append(count);
    return section;

    */
    const list = document.createElement('div');
    list.className = 'admin-compatible-vehicles';

    draft.compatible_vehicles = normalizeCompatibleVehiclesDraft(draft.compatible_vehicles);
    draft.compatible_vehicles.forEach((vehicle, index) => {
      list.append(
        createCompatibleVehicleRow(vehicle, index, draft.compatible_vehicles.length, {
          onBrandChange: (value) => {
            vehicle.car_brand_id = value;
            vehicle.car_model_id = '';
            vehicle.car_generation_id = '';
            rerender();
          },
          onModelChange: (value) => {
            vehicle.car_model_id = value;
            vehicle.car_generation_id = '';
            rerender();
          },
          onGenerationChange: (value) => {
            vehicle.car_generation_id = value;
          },
          onAdd: () => {
            draft.compatible_vehicles.push(createEmptyCompatibleVehicle());
            rerender();
          },
          onRemove: () => {
            draft.compatible_vehicles.splice(index, 1);
            rerender();
          },
        }),
      );
    });

    panel.append(list);
    return panel;
  }

  function createProductImagesEditor(draft) {
    const panel = document.createElement('div');
    panel.className = 'filter-card filter-card--dynamic admin-upload-panel';

    const head = document.createElement('div');
    head.className = 'filter-card__head';
    const title = document.createElement('h3');
    title.textContent = 'Изображения';
    head.append(title);

    const input = document.createElement('input');
    input.className = 'admin-upload-input';
    input.type = 'file';
    input.accept = 'image/*';
    input.multiple = true;

    const controls = document.createElement('div');
    controls.className = 'admin-upload-panel__controls';

    const trigger = createActionButton('Загрузить изображение', 'hero-link', () => {
      input.click();
    });

    const hint = document.createElement('p');
    hint.className = 'admin-upload-panel__hint';
    hint.textContent = 'Удаление и загрузка изображений применятся после сохранения товара.';

    controls.append(trigger, hint);

    const list = document.createElement('div');
    list.className = 'admin-upload-list';

    const renderDraftImages = () => {
      list.replaceChildren();

      const removedIds = new Set((draft.removed_image_ids || []).map((id) => String(id)));
      const existingImages = (draft.images || []).filter((image) => !removedIds.has(String(image.id)));
      const newImages = draft.new_images || [];

      if (!existingImages.length && !newImages.length) {
        const emptyState = document.createElement('p');
        emptyState.className = 'admin-upload-empty';
        emptyState.textContent = 'Изображения пока не выбраны.';
        list.append(emptyState);
        return;
      }

      existingImages.forEach((image) => {
        const item = document.createElement('div');
        item.className = 'admin-upload-item';

        const meta = document.createElement('div');
        meta.className = 'admin-upload-item__meta';

        const name = document.createElement('span');
        name.className = 'admin-upload-item__name';
        name.textContent = image.name || 'Изображение';

        const status = document.createElement('span');
        status.className = 'admin-upload-item__size';
        status.textContent = image.is_primary ? 'Текущее основное изображение' : 'Текущее изображение';

        meta.append(name, status);

        const removeButton = document.createElement('button');
        removeButton.type = 'button';
        removeButton.className = 'admin-upload-remove';
        removeButton.textContent = 'Удалить';
        removeButton.addEventListener('click', () => {
          draft.removed_image_ids = [...(draft.removed_image_ids || []), String(image.id)];
          renderDraftImages();
        });

        item.append(meta, removeButton);
        list.append(item);
      });

      newImages.forEach((file, index) => {
        const item = document.createElement('div');
        item.className = 'admin-upload-item';

        const meta = document.createElement('div');
        meta.className = 'admin-upload-item__meta';

        const name = document.createElement('span');
        name.className = 'admin-upload-item__name';
        name.textContent = file.name;

        const size = document.createElement('span');
        size.className = 'admin-upload-item__size';
        size.textContent = formatFileSize(file.size);

        meta.append(name, size);

        const removeButton = document.createElement('button');
        removeButton.type = 'button';
        removeButton.className = 'admin-upload-remove';
        removeButton.textContent = 'Удалить';
        removeButton.addEventListener('click', () => {
          draft.new_images.splice(index, 1);
          renderDraftImages();
        });

        item.append(meta, removeButton);
        list.append(item);
      });
    };

    input.addEventListener('change', () => {
      addDraftProductImages(draft, input.files || []);
      input.value = '';
      renderDraftImages();
    });

    renderDraftImages();
    panel.append(head, input, controls, list);
    return panel;
  }

  function formatAdminPrice(value) {
    const normalized = String(value ?? '').trim();
    return normalized ? `${normalized} ₽` : '—';
  }

  function renderProductsSection() {
    const section = sectionNodes.products;
    if (!section) return;
    section.list.replaceChildren();
    const query = state.manageSearch.products;

    if (!state.manage.products.length) {
      section.status.textContent = 'Товары не найдены.';
      showSectionList('products', false);
      return;
    }

    const filteredProducts = state.manage.products.filter((product) => matchesAdminName(product.name, query));
    if (!filteredProducts.length) {
      section.status.textContent = query ? 'Товары по вашему запросу не найдены.' : 'Товары не найдены.';
      showSectionList('products', false);
      return;
    }

    filteredProducts.forEach((product) => {
      const card = document.createElement('article');
      card.className = 'admin-entity-card';

      if (!product.isEditing) {
        const head = document.createElement('div');
        head.className = 'admin-entity-card__head';

        const titleBox = document.createElement('div');
        const title = document.createElement('h4');
        title.className = 'admin-entity-card__title';
        title.textContent = product.name;
        const subtitle = document.createElement('p');
        subtitle.className = 'admin-entity-card__subtitle';
        subtitle.textContent = `${product.brand || 'Без производителя'} • ${product.category_name || 'Без катагории'}`;
        titleBox.append(title, subtitle);

        const actions = document.createElement('div');
        actions.className = 'admin-entity-actions';
        actions.append(
          createActionButton('Редактировать', 'hero-link', () => {
            product.isEditing = true;
            product.draft = {
              name: product.name,
              short_description: product.short_description,
              description: product.description,
              article: product.article,
              vin_number: product.vin_number,
              price: product.price,
              stock_quantity: product.stock_quantity,
              brand_id: product.brand_id,
              compatible_vehicles: normalizeCompatibleVehiclesDraft(product.compatible_vehicles),
              category_id: product.category_id,
              characteristics: { ...(product.characteristics || {}) },
              images: cloneAdminProductImages(product.images),
              removed_image_ids: [],
              new_images: [],
            };
            renderProductsSection();
          }),
          createActionButton('Удалить', 'admin-danger-button', () => {
            openModal('Вы уверены, что хотите удалить этот пункт?', async () => {
              await postJson(buildItemEndpoint(endpoints.products, product.id, 'delete'), {});
              showNotice('Товар удалён.');
              await loadProductsSection();
            });
          }),
        );

        head.append(titleBox, actions);
        card.append(head);

        const grid = document.createElement('div');
        grid.className = 'admin-record-grid';
        grid.append(
          createRecordItem('Название', product.name),
          createRecordItem('Артикул', product.article),
          createRecordItem('VIN', product.vin_number),
          createRecordItem('Изображения', String((product.images || []).length || 0)),
          createRecordItem('Цена', formatAdminPrice(product.price)),
          createRecordItem('Количество в наличии', product.stock_quantity),
          createRecordItem('Производитель', product.brand),
          createRecordItem('Совместимые авто', formatCompatibleVehicles(product.compatible_vehicles), true),
          createRecordItem('Катагория', product.category_name),
        );
        card.append(grid);
      } else {
        const editor = document.createElement('div');
        editor.className = 'admin-inline-editor';

        const formGrid = document.createElement('div');
        formGrid.className = 'admin-form-grid';
        formGrid.append(
          createInputField('Название', product.draft.name, {
            onInput: (value) => {
              product.draft.name = value;
            },
          }),
          createInputField('Артикул', product.draft.article, {
            onInput: (value) => {
              product.draft.article = value;
            },
          }),
          createInputField('VIN', product.draft.vin_number, {
            onInput: (value) => {
              product.draft.vin_number = value;
            },
          }),
          createInputField('Цена', product.draft.price, {
            type: 'number',
            min: 0,
            step: '0.01',
            inputMode: 'decimal',
            onInput: (value) => {
              product.draft.price = value;
            },
          }),
          createInputField('Количество в наличии', product.draft.stock_quantity, {
            type: 'number',
            min: 0,
            step: '1',
            inputMode: 'numeric',
            onInput: (value) => {
              product.draft.stock_quantity = value;
            },
          }),
          createSelectField('Производитель', product.draft.brand_id, state.brands, 'Выберите производителя', (value) => {
            product.draft.brand_id = value;
          }),
          createSelectField('Катагория', product.draft.category_id, state.partTypes, 'Выберите катагорию', (value) => {
            product.draft.category_id = value;
            product.draft.characteristics = normalizeCharacteristicsForPartType(value, product.draft.characteristics);
            renderProductsSection();
          }),
          createTextareaField('Описание', product.draft.description, {
            rows: 5,
            onInput: (value) => {
              product.draft.description = value;
            },
          }),
        );
        editor.append(formGrid);
        editor.append(createProductCompatibleVehiclesEditor(product.draft, renderProductsSection));
        editor.append(createProductImagesEditor(product.draft));
        editor.append(createProductCharacteristicsEditor(product.draft, renderProductsSection));

        const actions = document.createElement('div');
        actions.className = 'admin-inline-editor__actions';
        actions.append(
          createActionButton('Сохранить', 'hero-button', async () => {
            await postFormData(
              buildItemEndpoint(endpoints.products, product.id, 'update'),
              buildProductUpdateFormData(product.draft),
            );
            showNotice('Товар обновлён.');
            await loadProductsSection();
          }),
          createActionButton('Отмена', 'hero-link', () => {
            product.isEditing = false;
            product.draft = null;
            renderProductsSection();
          }),
        );

        editor.append(actions);
        card.append(editor);
      }

      section.list.append(card);
    });

    showSectionList('products', true);
  }

  function createPartTypeDraft(partType) {
    return {
      name: partType.name,
      characteristics: (partType.characteristics || []).map((characteristic) => ({
        name: characteristic.name,
        values: characteristic.allows_custom_value
          ? [{ value: '', is_custom: true }]
          : characteristic.values.map((value) => ({ value, is_custom: false })),
      })),
    };
  }

  function ensurePartTypeDraftValueRows(group) {
    if (!group.values.length) {
      group.values.push({ value: '', is_custom: false });
    }
    if (group.values[0]?.is_custom) {
      group.values[0].value = '';
      group.values.forEach((valueItem, index) => {
        valueItem.is_custom = index === 0;
        if (index > 0) {
          valueItem.value = '';
        }
      });
    }
  }

  function createPartTypeOverview(partType) {
    const wrapper = document.createElement('div');
    wrapper.className = 'admin-characteristics-overview';

    if (!(partType.characteristics || []).length) {
      const empty = document.createElement('div');
      empty.className = 'admin-data-status';
      empty.textContent = 'У катагории пока нет характеристик.';
      wrapper.append(empty);
      return wrapper;
    }

    partType.characteristics.forEach((characteristic) => {
      const group = document.createElement('div');
      group.className = 'admin-characteristics-overview__group';

      const title = document.createElement('strong');
      title.textContent = characteristic.name;

      const values = document.createElement('div');
      values.className = 'admin-characteristics-overview__values';
      if (characteristic.allows_custom_value) {
        const chip = document.createElement('span');
        chip.className = 'admin-characteristics-chip';
        chip.textContent = 'Индивидуальное значение';
        values.append(chip);
      } else {
        (characteristic.values || []).forEach((value) => {
          const chip = document.createElement('span');
          chip.className = 'admin-characteristics-chip';
          chip.textContent = value;
          values.append(chip);
        });
      }

      group.append(title, values);
      wrapper.append(group);
    });

    return wrapper;
  }

  function renderPartTypeDraftEditor(partType) {
    const editor = document.createElement('div');
    editor.className = 'admin-inline-editor';

    editor.append(
      createInputField('Название катагории', partType.draft.name, {
        wide: true,
        onInput: (value) => {
          partType.draft.name = value;
        },
      }),
    );

    const section = document.createElement('div');
    section.className = 'admin-inline-editor__section admin-nested-panel';
    const title = document.createElement('h4');
    title.className = 'admin-inline-editor__title';
    title.textContent = 'Характеристики';
    section.append(title);

    const list = document.createElement('div');
    list.className = 'admin-characteristic-groups';

    partType.draft.characteristics.forEach((characteristic, characteristicIndex) => {
      ensurePartTypeDraftValueRows(characteristic);

      const group = document.createElement('div');
      group.className = 'filter-card admin-characteristic-editor';

      const head = document.createElement('div');
      head.className = 'admin-characteristic-editor__head';
      head.append(
        createInputField('Название характеристики', characteristic.name, {
          wide: true,
          onInput: (value) => {
            characteristic.name = value;
          },
        }),
      );
      const removeCharacteristicButton = createActionButton('Удалить характеристику', 'admin-mini-button', () => {
          partType.draft.characteristics.splice(characteristicIndex, 1);
          renderPartTypesSection();
        });
      removeCharacteristicButton.hidden = partType.draft.characteristics.length <= 1;
      head.append(removeCharacteristicButton);
      group.append(head);

      const values = document.createElement('div');
      values.className = 'admin-characteristic-editor__values';

      characteristic.values.forEach((valueItem, valueIndex) => {
        const row = document.createElement('div');
        row.className = 'admin-value-row admin-value-row--editable';
        const isGroupCustom = Boolean(characteristic.values[0]?.is_custom);

        const inputWrapper = document.createElement('div');
        inputWrapper.className = 'admin-value-row__input';
        const input = document.createElement('input');
        input.type = 'text';
        input.placeholder = 'Значение';
        input.value = valueItem.value || '';
        input.disabled = isGroupCustom;
        input.addEventListener('input', () => {
          valueItem.value = input.value;
        });
        inputWrapper.append(input);

        const actionSlot = document.createElement('div');
        actionSlot.className = 'admin-inline-action-slot';

        const addButton = createActionButton('+', 'admin-inline-add', () => {
          characteristic.values.push({ value: '', is_custom: false });
          renderPartTypesSection();
        });
        addButton.setAttribute('aria-label', 'Добавить значение');
        const addIcon = document.createElement('span');
        addIcon.className = 'admin-inline-add__icon';
        addIcon.setAttribute('aria-hidden', 'true');
        addButton.textContent = '';
        addButton.append(addIcon);

        const checkboxLabel = document.createElement('label');
        checkboxLabel.className = 'admin-checkbox';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = valueIndex === 0 && isGroupCustom;
        checkboxLabel.hidden = valueIndex !== 0;
        checkbox.addEventListener('change', () => {
          characteristic.values[0].is_custom = checkbox.checked;
          if (checkbox.checked) {
            characteristic.values.forEach((item, index) => {
              item.value = '';
              item.is_custom = index === 0;
            });
          } else {
            characteristic.values[0].is_custom = false;
          }
          renderPartTypesSection();
        });
        const checkboxText = document.createElement('span');
        checkboxText.textContent = 'Индивидуальное значение';
        checkboxLabel.append(checkbox, checkboxText);

        const removeButton = createActionButton('Удалить', 'admin-inline-remove', () => {
          characteristic.values.splice(valueIndex, 1);
          ensurePartTypeDraftValueRows(characteristic);
          renderPartTypesSection();
        });
        const removeIcon = document.createElement('span');
        removeIcon.className = 'admin-inline-add__icon admin-inline-add__icon--remove';
        removeIcon.setAttribute('aria-hidden', 'true');
        removeButton.textContent = '';
        removeButton.append(removeIcon);

        const isLastRow = valueIndex === characteristic.values.length - 1;
        const showAddButton = isLastRow && !isGroupCustom;
        const showRemoveButton = characteristic.values.length > 1 && !showAddButton;
        addButton.hidden = !showAddButton;
        removeButton.hidden = !showRemoveButton;
        actionSlot.hidden = !showAddButton && !showRemoveButton;
        addButton.classList.toggle('is-hidden', !showAddButton);
        removeButton.classList.toggle('is-hidden', !showRemoveButton);
        actionSlot.classList.toggle('is-hidden', !showAddButton && !showRemoveButton);

        if (!showAddButton && !showRemoveButton) {
          row.classList.add('admin-value-row--stacked');
        }

        actionSlot.append(addButton, removeButton);
        row.append(inputWrapper, actionSlot, checkboxLabel);
        values.append(row);
      });

      group.append(values);
      list.append(group);
    });

    section.append(list);
    section.append(
      createActionButton('Добавить характеристику', 'hero-link', () => {
        partType.draft.characteristics.push({
          name: '',
          values: [{ value: '', is_custom: false }],
        });
        renderPartTypesSection();
      }),
    );

    editor.append(section);

    const actions = document.createElement('div');
    actions.className = 'admin-inline-editor__actions';
    actions.append(
      createActionButton('Сохранить', 'hero-button', async () => {
        const payload = {
          name: partType.draft.name,
          characteristics: partType.draft.characteristics,
        };
        await postJson(buildItemEndpoint(endpoints.partTypes, partType.id, 'update'), payload);
        showNotice('Катагория обновлена.');
        await refreshPartTypesReferenceData();
        await loadPartTypesSection();
      }),
      createActionButton('Отмена', 'hero-link', () => {
        partType.isEditing = false;
        partType.draft = null;
        renderPartTypesSection();
      }),
    );

    editor.append(actions);
    return editor;
  }

  function renderPartTypesSection() {
    const section = sectionNodes.partTypes;
    if (!section) return;
    section.list.replaceChildren();
    const query = state.manageSearch.partTypes;

    if (!state.manage.partTypes.length) {
      section.status.textContent = 'Катагории не найдены.';
      showSectionList('partTypes', false);
      return;
    }

    const filteredPartTypes = state.manage.partTypes.filter((partType) => matchesAdminName(partType.name, query));
    if (!filteredPartTypes.length) {
      section.status.textContent = query ? 'Катагории по вашему запросу не найдены.' : 'Катагории не найдены.';
      showSectionList('partTypes', false);
      return;
    }

    filteredPartTypes.forEach((partType) => {
      const card = document.createElement('article');
      card.className = 'admin-entity-card';

      if (!partType.isEditing) {
        const head = document.createElement('div');
        head.className = 'admin-entity-card__head';

        const titleBox = document.createElement('div');
        const title = document.createElement('h4');
        title.className = 'admin-entity-card__title';
        title.textContent = partType.name;
        const subtitle = document.createElement('p');
        subtitle.className = 'admin-entity-card__subtitle';
        subtitle.textContent = `Характеристик: ${partType.characteristics.length}`;
        titleBox.append(title, subtitle);

        const actions = document.createElement('div');
        actions.className = 'admin-entity-actions';
        actions.append(
          createActionButton('Редактировать', 'hero-link', () => {
            partType.isEditing = true;
            partType.draft = createPartTypeDraft(partType);
            renderPartTypesSection();
          }),
          createActionButton('Удалить', 'admin-danger-button', () => {
            openModal('Вы уверены, что хотите удалить этот пункт?', async () => {
              await postJson(buildItemEndpoint(endpoints.partTypes, partType.id, 'delete'), {});
              showNotice('Катагория удалена.');
              await refreshPartTypesReferenceData();
              await loadPartTypesSection();
            });
          }),
        );

        head.append(titleBox, actions);
        card.append(head);
        card.append(createPartTypeOverview(partType));
      } else {
        card.append(renderPartTypeDraftEditor(partType));
      }

      section.list.append(card);
    });

    showSectionList('partTypes', true);
  }

  function renderBrandsSection() {
    const section = sectionNodes.brands;
    if (!section) return;
    section.list.replaceChildren();
    const query = state.manageSearch.brands;

    if (!state.manage.brands.length) {
      section.status.textContent = 'Производители не найдены.';
      showSectionList('brands', false);
      return;
    }

    const filteredBrands = state.manage.brands.filter((brand) => matchesAdminName(brand.name, query));
    if (!filteredBrands.length) {
      section.status.textContent = query ? 'Производители по вашему запросу не найдены.' : 'Производители не найдены.';
      showSectionList('brands', false);
      return;
    }

    filteredBrands.forEach((brand) => {
      const card = document.createElement('article');
      card.className = 'admin-entity-card';

      if (!brand.isEditing) {
        const head = document.createElement('div');
        head.className = 'admin-entity-card__head';

        const title = document.createElement('h4');
        title.className = 'admin-entity-card__title';
        title.textContent = brand.name;

        const actions = document.createElement('div');
        actions.className = 'admin-entity-actions';
        actions.append(
          createActionButton('Редактировать', 'hero-link', () => {
            brand.isEditing = true;
            brand.draft = { name: brand.name };
            renderBrandsSection();
          }),
          createActionButton('Удалить', 'admin-danger-button', () => {
            openModal('Вы уверены, что хотите удалить этот пункт?', async () => {
              await postJson(buildItemEndpoint(endpoints.brands, brand.id, 'delete'), {});
              showNotice('Производитель удалён.');
              await refreshBrandsReferenceData();
              await loadBrandsSection();
            });
          }),
        );

        head.append(title, actions);
        card.append(head);
      } else {
        const editor = document.createElement('div');
        editor.className = 'admin-inline-editor';
        editor.append(
          createInputField('Название производителя', brand.draft.name, {
            wide: true,
            onInput: (value) => {
              brand.draft.name = value;
            },
          }),
        );
        const actions = document.createElement('div');
        actions.className = 'admin-inline-editor__actions';
        actions.append(
          createActionButton('Сохранить', 'hero-button', async () => {
            await postJson(buildItemEndpoint(endpoints.brands, brand.id, 'update'), brand.draft);
            showNotice('Производитель обновлён.');
            await refreshBrandsReferenceData();
            await loadBrandsSection();
          }),
          createActionButton('Отмена', 'hero-link', () => {
            brand.isEditing = false;
            brand.draft = null;
            renderBrandsSection();
          }),
        );
        editor.append(actions);
        card.append(editor);
      }

      section.list.append(card);
    });

    showSectionList('brands', true);
  }

  function renderCarsSection() {
    const section = sectionNodes.cars;
    if (!section) return;
    section.list.replaceChildren();
    const query = state.manageSearch.cars;

    if (!state.manage.cars.length) {
      section.status.textContent = 'Марки автомобилей не найдены.';
      showSectionList('cars', false);
      return;
    }

    const filteredCars = state.manage.cars.filter((brand) => {
      if (matchesAdminName(brand.name, query)) return true;
      if ((brand.models || []).some((model) => matchesAdminName(model.name, query))) return true;
      return (brand.models || []).some((model) => (model.generations || []).some((generation) => matchesAdminName(generation.name, query)));
    });
    if (!filteredCars.length) {
      section.status.textContent = query ? 'Марки и модели по вашему запросу не найдены.' : 'Марки автомобилей не найдены.';
      showSectionList('cars', false);
      return;
    }

    filteredCars.forEach((brand) => {
      const card = document.createElement('article');
      card.className = 'admin-entity-card';

      if (!brand.isEditing) {
        const head = document.createElement('div');
        head.className = 'admin-entity-card__head';

        const titleBox = document.createElement('div');
        const title = document.createElement('h4');
        title.className = 'admin-entity-card__title';
        title.textContent = brand.name;
        const subtitle = document.createElement('p');
        subtitle.className = 'admin-entity-card__subtitle';
        subtitle.textContent = `Моделей: ${(brand.models || []).length}`;
        titleBox.append(title, subtitle);

        const actions = document.createElement('div');
        actions.className = 'admin-entity-actions';
        actions.append(
          createActionButton('Редактировать', 'hero-link', () => {
            brand.isEditing = true;
            brand.draft = { name: brand.name };
            renderCarsSection();
          }),
          createActionButton('Удалить', 'admin-danger-button', () => {
            openModal('Вы уверены, что хотите удалить этот пункт?', async () => {
              await postJson(buildItemEndpoint(endpoints.carBrands, brand.id, 'delete'), {});
              showNotice('Марка автомобиля удалена.');
              await refreshCarBrandsReferenceData();
              await loadCarsSection();
            });
          }),
        );

        head.append(titleBox, actions);
        card.append(head);

        const modelsList = document.createElement('div');
        modelsList.className = 'admin-model-list';

        if (!(brand.models || []).length) {
          const empty = document.createElement('div');
          empty.className = 'admin-data-status';
          empty.textContent = 'У этой марки пока нет моделей.';
          modelsList.append(empty);
        } else {
          brand.models.forEach((model) => {
            const modelCard = document.createElement('div');
            modelCard.className = 'admin-model-card';

            if (!model.isEditing) {
              const modelHead = document.createElement('div');
              modelHead.className = 'admin-model-card__head';

              const modelMeta = document.createElement('div');
              modelMeta.className = 'admin-model-card__meta';

              const modelTitle = document.createElement('h5');
              modelTitle.className = 'admin-model-card__title';
              modelTitle.textContent = model.name;

              const modelSubtitle = document.createElement('p');
              modelSubtitle.className = 'admin-model-card__subtitle';
              modelSubtitle.textContent = `Марка: ${brand.name} • Поколений: ${(model.generations || []).length}`;

              modelMeta.append(modelTitle, modelSubtitle);

              const modelActions = document.createElement('div');
              modelActions.className = 'admin-entity-actions';
              modelActions.append(
                createActionButton('Редактировать', 'hero-link', () => {
                  model.isEditing = true;
                  model.draft = {
                    name: model.name,
                    brand_id: String(model.brand_id || ''),
                  };
                  renderCarsSection();
                }),
                createActionButton('Удалить', 'admin-danger-button', () => {
                  openModal('Вы уверены, что хотите удалить этот пункт?', async () => {
                    await postJson(buildItemEndpoint(endpoints.carModels, model.id, 'delete'), {});
                    showNotice('Модель автомобиля удалена.');
                    await refreshCarBrandsReferenceData();
                    await loadCarsSection();
                  });
                }),
              );

              modelHead.append(modelMeta, modelActions);
              modelCard.append(modelHead);

              const generationsList = document.createElement('div');
              generationsList.className = 'admin-generation-list';

              if (!(model.generations || []).length) {
                const emptyGenerations = document.createElement('div');
                emptyGenerations.className = 'admin-data-status';
                emptyGenerations.textContent = 'У этой модели пока нет поколений.';
                generationsList.append(emptyGenerations);
              } else {
                model.generations.forEach((generation) => {
                  const generationCard = document.createElement('div');
                  generationCard.className = 'admin-generation-card';

                  if (!generation.isEditing) {
                    const generationHead = document.createElement('div');
                    generationHead.className = 'admin-model-card__head';

                    const generationMeta = document.createElement('div');
                    generationMeta.className = 'admin-model-card__meta';

                    const generationTitle = document.createElement('h6');
                    generationTitle.className = 'admin-generation-card__title';
                    generationTitle.textContent = generation.name;

                    const generationSubtitle = document.createElement('p');
                    generationSubtitle.className = 'admin-model-card__subtitle';
                    generationSubtitle.textContent = `Модель: ${model.name}`;

                    generationMeta.append(generationTitle, generationSubtitle);

                    const generationActions = document.createElement('div');
                    generationActions.className = 'admin-entity-actions';
                    generationActions.append(
                      createActionButton('Редактировать', 'hero-link', () => {
                        generation.isEditing = true;
                        generation.draft = {
                          name: generation.name,
                          brand_id: String(generation.brand_id || ''),
                          model_id: String(generation.model_id || ''),
                        };
                        renderCarsSection();
                      }),
                      createActionButton('Удалить', 'admin-danger-button', () => {
                        openModal('Вы уверены, что хотите удалить этот пункт?', async () => {
                          await postJson(buildItemEndpoint(endpoints.carGenerations, generation.id, 'delete'), {});
                          showNotice('Поколение автомобиля удалено.');
                          await refreshCarBrandsReferenceData();
                          await loadCarsSection();
                        });
                      }),
                    );

                    generationHead.append(generationMeta, generationActions);
                    generationCard.append(generationHead);
                  } else {
                    const generationEditor = document.createElement('div');
                    generationEditor.className = 'admin-inline-editor admin-inline-editor--compact';

                    const generationGrid = document.createElement('div');
                    generationGrid.className = 'admin-form-grid';
                    generationGrid.append(
                      createSelectField('Марка автомобиля', generation.draft.brand_id, state.carBrands, 'Выберите марку автомобиля', (value) => {
                        generation.draft.brand_id = value;
                        generation.draft.model_id = '';
                        renderCarsSection();
                      }),
                      createSelectField(
                        'Модель автомобиля',
                        generation.draft.model_id,
                        (getCarBrandById(generation.draft.brand_id)?.models || []).map((item) => ({
                          id: item.id,
                          name: item.name,
                        })),
                        'Выберите модель автомобиля',
                        (value) => {
                          generation.draft.model_id = value;
                        },
                      ),
                      createInputField('Поколение автомобиля', generation.draft.name, {
                        onInput: (value) => {
                          generation.draft.name = value;
                        },
                      }),
                    );
                    generationEditor.append(generationGrid);

                    const generationActions = document.createElement('div');
                    generationActions.className = 'admin-inline-editor__actions';
                    generationActions.append(
                      createActionButton('Сохранить', 'hero-button', async () => {
                        await postJson(buildItemEndpoint(endpoints.carGenerations, generation.id, 'update'), generation.draft);
                        showNotice('Поколение автомобиля обновлено.');
                        await refreshCarBrandsReferenceData();
                        await loadCarsSection();
                      }),
                      createActionButton('Отмена', 'hero-link', () => {
                        generation.isEditing = false;
                        generation.draft = null;
                        renderCarsSection();
                      }),
                    );

                    generationEditor.append(generationActions);
                    generationCard.append(generationEditor);
                  }

                  generationsList.append(generationCard);
                });
              }

              modelCard.append(generationsList);
            } else {
              const editor = document.createElement('div');
              editor.className = 'admin-inline-editor admin-inline-editor--compact';

              const grid = document.createElement('div');
              grid.className = 'admin-form-grid';
              grid.append(
                createSelectField('Марка автомобиля', model.draft.brand_id, state.carBrands, 'Выберите марку автомобиля', (value) => {
                  model.draft.brand_id = value;
                }),
                createInputField('Модель автомобиля', model.draft.name, {
                  onInput: (value) => {
                    model.draft.name = value;
                  },
                }),
              );
              editor.append(grid);

              const actions = document.createElement('div');
              actions.className = 'admin-inline-editor__actions';
              actions.append(
                createActionButton('Сохранить', 'hero-button', async () => {
                  await postJson(buildItemEndpoint(endpoints.carModels, model.id, 'update'), model.draft);
                  showNotice('Модель автомобиля обновлена.');
                  await refreshCarBrandsReferenceData();
                  await loadCarsSection();
                }),
                createActionButton('Отмена', 'hero-link', () => {
                  model.isEditing = false;
                  model.draft = null;
                  renderCarsSection();
                }),
              );

              editor.append(actions);
              modelCard.append(editor);
            }

            modelsList.append(modelCard);
          });
        }

        card.append(modelsList);
      } else {
        const editor = document.createElement('div');
        editor.className = 'admin-inline-editor';
        editor.append(
          createInputField('Марка автомобиля', brand.draft.name, {
            wide: true,
            onInput: (value) => {
              brand.draft.name = value;
            },
          }),
        );

        const actions = document.createElement('div');
        actions.className = 'admin-inline-editor__actions';
        actions.append(
          createActionButton('Сохранить', 'hero-button', async () => {
            await postJson(buildItemEndpoint(endpoints.carBrands, brand.id, 'update'), brand.draft);
            showNotice('Марка автомобиля обновлена.');
            await refreshCarBrandsReferenceData();
            await loadCarsSection();
          }),
          createActionButton('Отмена', 'hero-link', () => {
            brand.isEditing = false;
            brand.draft = null;
            renderCarsSection();
          }),
        );
        editor.append(actions);
        card.append(editor);
      }

      section.list.append(card);
    });

    showSectionList('cars', true);
  }

  function createUserOrdersOverview(orders) {
    const section = document.createElement('div');
    section.className = 'admin-inline-editor__section';

    const title = document.createElement('h4');
    title.className = 'admin-inline-editor__title';
    title.textContent = 'История заказов';
    section.append(title);

    if (!orders.length) {
      const empty = document.createElement('div');
      empty.className = 'admin-data-status';
      empty.textContent = 'У пользователя пока нет заказов.';
      section.append(empty);
      return section;
    }

    const count = document.createElement('div');
    count.className = 'admin-data-status';
    count.textContent = `Количество заказов: ${orders.length}`;
    section.append(count);
    return section;

    const list = document.createElement('div');
    list.className = 'admin-user-orders';

    orders.forEach((order) => {
      const card = document.createElement('div');
      card.className = 'admin-order-card';

      const head = document.createElement('div');
      head.className = 'admin-order-card__head';

      const headingBox = document.createElement('div');
      const heading = document.createElement('h4');
      heading.className = 'admin-order-card__title';
      heading.textContent = `Заказ #${order.id}`;
      const meta = document.createElement('p');
      meta.className = 'admin-order-card__meta';
      meta.textContent = order.created_at_display || 'Дата не указана';
      headingBox.append(heading, meta);
      head.append(headingBox);

      const grid = document.createElement('div');
      grid.className = 'admin-record-grid';
      grid.append(
        createRecordItem('Статус', getOrderStatusLabel(order.status)),
        createRecordItem('Сумма', formatAdminOrderTotal(order.total)),
        createRecordItem('Получатель', order.full_name),
        createRecordItem('Телефон', order.phone),
        createRecordItem('Адрес', [order.region, order.city, order.address].filter(Boolean).join(', '), true),
        createRecordItem('Товары', formatAdminOrderItemsSummary(order.items), true),
      );

      card.append(head, grid);
      list.append(card);
    });

    section.append(list);
    return section;
  }

  function createUserOrderItemEditor(order, item, itemIndex, rerender) {
    const card = document.createElement('div');
    card.className = 'admin-order-item';

    const grid = document.createElement('div');
    grid.className = 'admin-form-grid';
    grid.append(
      createInputField('ID товара', item.product_id, {
        onInput: (value) => {
          item.product_id = value;
        },
      }),
      createInputField('Название товара', item.name, {
        onInput: (value) => {
          item.name = value;
        },
      }),
      createInputField('Количество', item.quantity, {
        type: 'number',
        min: 1,
        step: 1,
        inputMode: 'numeric',
        onInput: (value) => {
          item.quantity = value;
        },
      }),
      createInputField('Цена', item.price, {
        type: 'number',
        min: 0,
        step: 0.01,
        inputMode: 'decimal',
        onInput: (value) => {
          item.price = value;
        },
      }),
    );
    card.append(grid);

    const actions = document.createElement('div');
    actions.className = 'admin-mini-actions';
    const removeButton = createActionButton('Удалить товар', 'admin-mini-button', () => {
      order.items.splice(itemIndex, 1);
      if (!order.items.length) {
        order.items.push(createEmptyOrderItemDraft());
      }
      rerender();
    });
    removeButton.hidden = order.items.length <= 1;
    actions.append(removeButton);
    card.append(actions);
    return card;
  }

  function createUserOrderEditor(order, orders, rerender) {
    const card = document.createElement('div');
    card.className = 'admin-order-card';

    const head = document.createElement('div');
    head.className = 'admin-order-card__head';

    const headingBox = document.createElement('div');
    const heading = document.createElement('h4');
    heading.className = 'admin-order-card__title';
    heading.textContent = `Заказ #${order.id}`;
    const meta = document.createElement('p');
    meta.className = 'admin-order-card__meta';
    meta.textContent = order.created_at_display || 'Дата не указана';
    headingBox.append(heading, meta);
    head.append(headingBox);

    const headActions = document.createElement('div');
    headActions.className = 'admin-mini-actions';
    headActions.append(
      createActionButton('Удалить заказ', 'admin-mini-button', () => {
        const nextOrders = orders.filter((item) => String(item?.id || '') !== String(order?.id || ''));
        if (nextOrders.length !== orders.length) {
          replaceArrayContents(orders, nextOrders);
          rerender();
        }
      }),
    );
    head.append(headActions);
    card.append(head);

    const grid = document.createElement('div');
    grid.className = 'admin-form-grid';
    grid.append(
      createInputField('Получатель', order.full_name, {
        onInput: (value) => {
          order.full_name = value;
        },
      }),
      createInputField('Телефон', order.phone, {
        onInput: (value) => {
          order.phone = value;
        },
      }),
      createInputField('Регион', order.region, {
        onInput: (value) => {
          order.region = value;
        },
      }),
      createInputField('Город', order.city, {
        onInput: (value) => {
          order.city = value;
        },
      }),
      createInputField('Сумма', order.total, {
        type: 'number',
        min: 0,
        step: 0.01,
        inputMode: 'decimal',
        onInput: (value) => {
          order.total = value;
        },
      }),
      createSelectField('Статус', order.status, orderStatusOptions, 'Выберите статус', (value) => {
        order.status = value;
      }),
    );
    card.append(grid);

    card.append(
      createTextareaField('Адрес', order.address, {
        rows: 3,
        onInput: (value) => {
          order.address = value;
        },
      }),
    );

    const itemsSection = document.createElement('div');
    itemsSection.className = 'admin-inline-editor__section';

    const itemsTitle = document.createElement('h4');
    itemsTitle.className = 'admin-inline-editor__title';
    itemsTitle.textContent = 'Товары в заказе';
    itemsSection.append(itemsTitle);

    const itemsList = document.createElement('div');
    itemsList.className = 'admin-order-items';
    order.items.forEach((item, itemIndex) => {
      itemsList.append(createUserOrderItemEditor(order, item, itemIndex, rerender));
    });
    itemsSection.append(itemsList);

    const itemsActions = document.createElement('div');
    itemsActions.className = 'admin-mini-actions';
    itemsActions.append(
      createActionButton('Добавить товар', 'admin-mini-button admin-mini-button--neutral', () => {
        order.items.push(createEmptyOrderItemDraft());
        rerender();
      }),
    );
    itemsSection.append(itemsActions);

    card.append(itemsSection);
    return card;
  }

  function createUserOrdersEditor(orders, rerender) {
    const section = document.createElement('div');
    section.className = 'admin-inline-editor__section admin-nested-panel';

    const title = document.createElement('h4');
    title.className = 'admin-inline-editor__title';
    title.textContent = 'История заказов';
    section.append(title);

    if (!orders.length) {
      const empty = document.createElement('div');
      empty.className = 'admin-data-status';
      empty.textContent = 'У пользователя пока нет заказов.';
      section.append(empty);
      return section;
    }

    const list = document.createElement('div');
    list.className = 'admin-user-orders';
    orders.forEach((order) => {
      list.append(createUserOrderEditor(order, orders, rerender));
    });
    section.append(list);
    return section;
  }

  async function saveManagedUserChanges(managedUser) {
    try {
      const response = await postJson(buildItemEndpoint(endpoints.users, managedUser.id, 'update'), managedUser.draft);
      managedUser.name = response.user?.name || managedUser.draft.name;
      managedUser.email = response.user?.email || managedUser.draft.email;
      managedUser.role = response.user?.role || managedUser.draft.role;
      managedUser.orders = cloneAdminOrders(response.user?.orders);
      managedUser.isEditing = false;
      managedUser.draft = null;
      showNotice('Пользователь обновлён.');
      renderUsersSection();
    } catch (error) {
      showNotice(error.message || 'Не удалось сохранить изменения пользователя.', 'error');
    }
  }

  function createProductCompatibleVehiclesEditor(draft, rerender) {
    const panel = document.createElement('div');
    panel.className = 'filter-card filter-card--dynamic admin-vehicle-panel';

    const head = document.createElement('div');
    head.className = 'filter-card__head';
    const title = document.createElement('h3');
    title.textContent = 'Совместимые авто';
    head.append(title);
    panel.append(head);

    const list = document.createElement('div');
    list.className = 'admin-compatible-vehicles';

    draft.compatible_vehicles = normalizeCompatibleVehiclesDraft(draft.compatible_vehicles);
    draft.compatible_vehicles.forEach((vehicle, index) => {
      list.append(
        createCompatibleVehicleRow(vehicle, index, draft.compatible_vehicles.length, {
          onBrandChange: (value) => {
            vehicle.car_brand_id = value;
            vehicle.car_model_id = '';
            vehicle.car_generation_id = '';
            rerender();
          },
          onModelChange: (value) => {
            vehicle.car_model_id = value;
            vehicle.car_generation_id = '';
            rerender();
          },
          onGenerationChange: (value) => {
            vehicle.car_generation_id = value;
          },
          onAdd: () => {
            draft.compatible_vehicles.push(createEmptyCompatibleVehicle());
            rerender();
          },
          onRemove: () => {
            draft.compatible_vehicles.splice(index, 1);
            rerender();
          },
        }),
      );
    });

    panel.append(list);
    return panel;
  }

  function createUserOrdersOverview(orders) {
    const section = document.createElement('div');
    section.className = 'admin-inline-editor__section';

    const title = document.createElement('h4');
    title.className = 'admin-inline-editor__title';
    title.textContent = 'История заказов';
    section.append(title);

    if (!orders.length) {
      const empty = document.createElement('div');
      empty.className = 'admin-data-status';
      empty.textContent = 'У пользователя пока нет заказов.';
      section.append(empty);
      return section;
    }

    const count = document.createElement('div');
    count.className = 'admin-data-status';
    count.textContent = `Количество заказов: ${orders.length}`;
    section.append(count);
    return section;
  }

  function renderUsersSection() {
    {
      const sectionNode = sectionNodes.users;
      if (!sectionNode) return;
      sectionNode.list.replaceChildren();
      const searchQuery = state.manageSearch.users;

      if (!state.manage.users.length) {
        sectionNode.status.textContent = 'Пользователи не найдены.';
        showSectionList('users', false);
        return;
      }

      const visibleUsers = state.manage.users.filter((item) => matchesAdminName(item.name, searchQuery));
      if (!visibleUsers.length) {
        sectionNode.status.textContent = searchQuery ? 'Пользователи по вашему запросу не найдены.' : 'Пользователи не найдены.';
        showSectionList('users', false);
        return;
      }

      visibleUsers.forEach((managedUser) => {
        const userCard = document.createElement('article');
        userCard.className = 'admin-entity-card';

        const head = document.createElement('div');
        head.className = 'admin-entity-card__head';

        const headingBox = document.createElement('div');
        const title = document.createElement('h3');
        title.className = 'admin-entity-card__title';
        title.textContent = managedUser.name;
        const subtitle = document.createElement('p');
        subtitle.className = 'admin-entity-card__subtitle';
        subtitle.textContent = `Заказов: ${(managedUser.isEditing ? managedUser.draft.orders : managedUser.orders).length}`;
        headingBox.append(title, subtitle);
        head.append(headingBox);

        if (!managedUser.isEditing) {
          const actions = document.createElement('div');
          actions.className = 'admin-entity-actions';
          actions.append(
            createActionButton('Редактировать', 'hero-link', () => {
              managedUser.isEditing = true;
              managedUser.draft = {
                name: managedUser.name,
                email: managedUser.email,
                role: managedUser.role,
                orders: cloneAdminOrders(managedUser.orders),
              };
              renderUsersSection();
            }),
            createActionButton('Удалить', 'admin-danger-button', () => {
              openModal('Вы уверены, что хотите удалить этот пункт?', async () => {
                await postJson(buildItemEndpoint(endpoints.users, managedUser.id, 'delete'), {});
                showNotice('Пользователь удалён.');
                await loadUsersSection();
              });
            }),
          );
          head.append(actions);

          const grid = document.createElement('div');
          grid.className = 'admin-record-grid';
          grid.append(
            createRecordItem('Имя', managedUser.name),
            createRecordItem('Email', managedUser.email),
            createRecordItem('Роль', managedUser.role),
          );
          userCard.append(head, grid, createUserOrdersOverview(managedUser.orders));
        } else {
          const editor = document.createElement('div');
          editor.className = 'admin-inline-editor';

          const grid = document.createElement('div');
          grid.className = 'admin-form-grid';
          grid.append(
            createInputField('Имя', managedUser.draft.name, {
              onInput: (value) => {
                managedUser.draft.name = value;
              },
            }),
            createInputField('Email', managedUser.draft.email, {
              type: 'email',
              onInput: (value) => {
                managedUser.draft.email = value;
              },
            }),
            createRoleSelectField('Роль', managedUser.draft.role, (value) => {
              managedUser.draft.role = value;
            }),
          );
          editor.append(grid);
          editor.append(createUserOrdersEditor(managedUser.draft.orders, renderUsersSection));

          const actions = document.createElement('div');
          actions.className = 'admin-inline-editor__actions';
          actions.append(
            createActionButton('Сохранить', 'hero-button', async () => {
              await saveManagedUserChanges(managedUser);
              return;
              showNotice('Пользователь обновлён.');
              await loadUsersSection();
            }),
            createActionButton('Отмена', 'hero-link', () => {
              managedUser.isEditing = false;
              managedUser.draft = null;
              renderUsersSection();
            }),
          );
          editor.append(actions);
          userCard.append(head, editor);
        }

        sectionNode.list.append(userCard);
      });

      showSectionList('users', true);
      return;
    }
    const section = sectionNodes.users;
    if (!section) return;
    section.list.replaceChildren();
    const query = state.manageSearch.users;

    if (!state.manage.users.length) {
      section.status.textContent = 'Пользователи не найдены.';
      showSectionList('users', false);
      return;
    }

    const filteredUsers = state.manage.users.filter((user) => matchesAdminName(user.name, query));
    if (!filteredUsers.length) {
      section.status.textContent = query ? 'Пользователи по вашему запросу не найдены.' : 'Пользователи не найдены.';
      showSectionList('users', false);
      return;
    }

    filteredUsers.forEach((user) => {
      const card = document.createElement('article');
      card.className = 'admin-entity-card';

      if (!user.isEditing) {
        const actions = document.createElement('div');
        actions.className = 'admin-entity-actions';
        actions.append(
          createActionButton('Редактировать', 'hero-link', () => {
            user.isEditing = true;
            user.draft = {
              name: user.name,
              email: user.email,
              role: user.role,
            };
            renderUsersSection();
          }),
          createActionButton('Удалить', 'admin-danger-button', () => {
            openModal('Вы уверены, что хотите удалить этот пункт?', async () => {
              await postJson(buildItemEndpoint(endpoints.users, user.id, 'delete'), {});
              showNotice('Пользователь удалён.');
              await loadUsersSection();
            });
          }),
        );

        const grid = document.createElement('div');
        grid.className = 'admin-record-grid';
        grid.append(
          createRecordItem('Имя', user.name),
          createRecordItem('Email', user.email),
          createRecordItem('Роль', user.role),
        );
        card.append(grid);
        card.append(actions);
      } else {
        const editor = document.createElement('div');
        editor.className = 'admin-inline-editor';
        const grid = document.createElement('div');
        grid.className = 'admin-form-grid';
        grid.append(
          createInputField('Имя', user.draft.name, {
            onInput: (value) => {
              user.draft.name = value;
            },
          }),
          createInputField('Email', user.draft.email, {
            type: 'email',
            onInput: (value) => {
              user.draft.email = value;
            },
          }),
          createRoleSelectField('Роль', user.draft.role, (value) => {
            user.draft.role = value;
          }),
        );
        editor.append(grid);

        const actions = document.createElement('div');
        actions.className = 'admin-inline-editor__actions';
        actions.append(
          createActionButton('Сохранить', 'hero-button', async () => {
            await postJson(buildItemEndpoint(endpoints.users, user.id, 'update'), user.draft);
            showNotice('Пользователь обновлён.');
            await loadUsersSection();
          }),
          createActionButton('Отмена', 'hero-link', () => {
            user.isEditing = false;
            user.draft = null;
            renderUsersSection();
          }),
        );
        editor.append(actions);
        card.append(editor);
      }

      section.list.append(card);
    });

    showSectionList('users', true);
  }

  tabs.forEach((tab) => {
    tab.addEventListener('click', () => switchSection(tab.dataset.adminTab));
  });

  productsSearchInput?.addEventListener('input', () => {
    state.manageSearch.products = normalizeAdminSearch(productsSearchInput.value);
    renderProductsSection();
  });

  partTypesSearchInput?.addEventListener('input', () => {
    state.manageSearch.partTypes = normalizeAdminSearch(partTypesSearchInput.value);
    renderPartTypesSection();
  });

  brandsSearchInput?.addEventListener('input', () => {
    state.manageSearch.brands = normalizeAdminSearch(brandsSearchInput.value);
    renderBrandsSection();
  });

  carsSearchInput?.addEventListener('input', () => {
    state.manageSearch.cars = normalizeAdminSearch(carsSearchInput.value);
    renderCarsSection();
  });

  usersSearchInput?.addEventListener('input', () => {
    state.manageSearch.users = normalizeAdminSearch(usersSearchInput.value);
    renderUsersSection();
  });

  navToggleButton?.addEventListener('click', () => {
    setAdminNavOpen(!navShell.classList.contains('is-open'));
  });

  window.addEventListener('resize', () => {
    if (!isMobileAdminNav()) {
      setAdminNavOpen(false);
    }
  });

  productPartTypeSelect?.addEventListener('change', renderCreateProductCharacteristics);

  productImagesTrigger?.addEventListener('click', () => {
    productImagesInput?.click();
  });

  productImagesInput?.addEventListener('change', () => {
    if (productImagesInput.files?.length) {
      addSelectedProductImages(productImagesInput.files);
      productImagesInput.value = '';
    }
  });

  addCharacteristicGroupButton?.addEventListener('click', () => {
    characteristicGroups?.append(createCharacteristicGroup());
    syncCharacteristicGroupButtons();
    syncInlineAddButtons();
  });

  brandForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      const payload = {
        name: brandForm.querySelector('input[name="name"]')?.value.trim() || '',
      };
      await postJson(endpoints.brands, payload);
      await refreshBrandsReferenceData();
      brandForm.reset();
      showNotice('Производитель добавлен.');
      if (state.currentSection === 'brands') {
        await loadBrandsSection();
      }
    } catch (error) {
      showNotice(error.message, 'error');
    }
  });

  carBrandInput?.addEventListener('input', syncCarFormButtons);
  carModelBrandSelect?.addEventListener('change', syncCarFormButtons);
  carModelInput?.addEventListener('input', syncCarFormButtons);
  carGenerationBrandSelect?.addEventListener('change', () => {
    renderCarGenerationModelSelect();
    syncCarFormButtons();
  });
  carGenerationModelSelect?.addEventListener('change', syncCarFormButtons);
  carGenerationInput?.addEventListener('input', syncCarFormButtons);

  carBrandForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      await postJson(endpoints.carBrands, {
        name: carBrandInput?.value.trim() || '',
      });
      await refreshCarBrandsReferenceData();
      carBrandForm.reset();
      syncCarFormButtons();
      showNotice('Марка автомобиля добавлена.');
      if (state.currentSection === 'cars') {
        await loadCarsSection();
      }
    } catch (error) {
      showNotice(error.message, 'error');
    }
  });

  carModelForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      await postJson(endpoints.carModels, {
        brand_id: carModelBrandSelect?.value || '',
        name: carModelInput?.value.trim() || '',
      });
      await refreshCarBrandsReferenceData();
      carModelInput.value = '';
      syncCarFormButtons();
      showNotice('Модель автомобиля добавлена.');
      if (state.currentSection === 'cars') {
        await loadCarsSection();
      }
    } catch (error) {
      showNotice(error.message, 'error');
    }
  });

  carGenerationForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      await postJson(endpoints.carGenerations, {
        brand_id: carGenerationBrandSelect?.value || '',
        model_id: carGenerationModelSelect?.value || '',
        name: carGenerationInput?.value.trim() || '',
      });
      await refreshCarBrandsReferenceData();
      carGenerationInput.value = '';
      syncCarFormButtons();
      showNotice('Поколение автомобиля добавлено.');
    } catch (error) {
      showNotice(error.message, 'error');
    }
  });

  partTypeForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      await postJson(endpoints.partTypes, collectPartTypePayload());
      partTypeForm.reset();
      characteristicGroups.replaceChildren();
      characteristicGroups.append(createCharacteristicGroup());
      syncCharacteristicGroupButtons();
      syncInlineAddButtons();
      await refreshPartTypesReferenceData();
      showNotice('Катагория добавлена.');
      if (state.currentSection === 'part-types') {
        await loadPartTypesSection();
      }
    } catch (error) {
      showNotice(error.message, 'error');
    }
  });

  productForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      await postFormData(endpoints.products, buildProductFormData());
      productForm.reset();
      clearSelectedProductImages();
      productCompatibleVehiclesDraft = [createEmptyCompatibleVehicle()];
      renderProductSelects();
      renderProductCompatibleVehicles();
      renderCreateProductCharacteristics();
      productCharacteristicsSection.hidden = true;
      showNotice('Товар добавлен.');
      if (state.currentSection === 'products') {
        await loadProductsSection();
      }
    } catch (error) {
      showNotice(error.message, 'error');
    }
  });

  modalCloseButtons.forEach((button) => {
    button.addEventListener('click', closeModal);
  });
  modalConfirmButton?.addEventListener('click', confirmModalAction);

  syncStickyOffset();
  setAdminNavOpen(false);
  renderProductSelects();
  productCompatibleVehiclesDraft = [createEmptyCompatibleVehicle()];
  renderProductCompatibleVehicles();
  renderCarBrandSelect();
  renderCarGenerationBrandSelect();
  renderCarGenerationModelSelect();
  renderCreateProductCharacteristics();
  renderSelectedProductImages();
  syncCarFormButtons();
  characteristicGroups?.append(createCharacteristicGroup());
  syncCharacteristicGroupButtons();
  syncInlineAddButtons();
  switchSection('create-product');

  window.addEventListener('resize', syncStickyOffset);
})();
