const metaScript = document.getElementById("adminMeta");
if (!metaScript) {
  throw new Error("Không tìm thấy dữ liệu meta cho admin console.");
}
const adminMeta = JSON.parse(metaScript.textContent || "{}");
const tabsContainer = document.getElementById("adminTabs");
const tableHead = document.querySelector("[data-admin='table-head']");
const tableBody = document.querySelector("[data-admin='table-body']");
const tableEmpty = document.querySelector("[data-admin='empty']");
const entityLabel = document.querySelector("[data-admin='entityLabel']");
const entityDescription = document.querySelector("[data-admin='entityDescription']");
const form = document.getElementById("adminEntityForm");
const formFields = document.querySelector("[data-admin='form-fields']");
const formTitle = document.querySelector("[data-admin='form-title']");
const formDescription = document.querySelector("[data-admin='form-description']");
const formResetBtn = document.querySelector("[data-admin='form-reset']");
const formDeleteBtn = document.querySelector("[data-admin='form-delete']");
const toastEl = document.querySelector("[data-admin='toast']");
let activeEntity = adminMeta.entities?.[0] || null;
let items = [];
let editingId = null;

const getCookie = (name) => {
  if (!document.cookie) return null;
  const cookies = document.cookie.split(";");
  for (let cookie of cookies) {
    const [key, value] = cookie.trim().split("=");
    if (key === name) return decodeURIComponent(value);
  }
  return null;
};

const csrfToken =
  document.querySelector('meta[name="csrf-token"]')?.getAttribute("content") ||
  getCookie("csrftoken");

const logCsrfState = () => {
  console.debug("[admin-console] CSRF state", {
    csrfToken,
    cookieToken: getCookie("csrftoken"),
    tokensMatch: getCookie("csrftoken") === csrfToken,
  });
};

const extractErrorDetail = async (response) => {
  const data = await response.json().catch(() => ({}));
  const detail = data.error || data.detail || response.statusText || "Đã có lỗi xảy ra.";
  if (response.status === 403) {
    console.warn("[admin-console] CSRF error", detail);
  }
  return detail;
};

const showToast = (message, variant = "success") => {
  if (!toastEl) return;
  toastEl.textContent = message;
  toastEl.className = "admin-console-toast";
  toastEl.classList.add("active", variant);
  setTimeout(() => {
    toastEl.classList.remove("active", "success", "error");
  }, 3500);
};

const renderTabs = () => {
  if (!tabsContainer || !adminMeta.entities) return;
  tabsContainer.innerHTML = "";
  adminMeta.entities.forEach((entity) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "admin-console-tab";
    btn.textContent = entity.label;
    btn.dataset.entityKey = entity.key;
    if (activeEntity && entity.key === activeEntity.key) {
      btn.classList.add("active");
    }
    btn.addEventListener("click", () => switchEntity(entity.key));
    tabsContainer.appendChild(btn);
  });
};

const getEntityMeta = (key) => adminMeta.entities?.find((entity) => entity.key === key) || null;

const switchEntity = (key) => {
  const entity = getEntityMeta(key);
  if (!entity) return;
  activeEntity = entity;
  editingId = null;
  renderTabs();
  renderFormFields();
  entityLabel.textContent = entity.label;
  entityDescription.textContent = entity.description || "";
  formDeleteBtn.style.display = "none";
  formTitle.textContent = `Tạo mới ${entity.label}`;
  formDescription.textContent = entity.description || "";
  fetchList();
};

const fetchList = async () => {
  if (!activeEntity) return;
  tableBody.innerHTML = "";
  tableHead.innerHTML = "";
  tableEmpty.textContent = "Đang tải dữ liệu...";
  tableEmpty.style.display = "block";
  try {
    const response = await fetch(activeEntity.endpoints.collection, {
      headers: {
        Accept: "application/json",
      },
      credentials: "same-origin",
    });
    if (!response.ok) {
      throw new Error("Không thể tải dữ liệu.");
    }
    const payload = await response.json();
    items = payload.results || payload;
    renderTable();
  } catch (error) {
    showToast(error.message, "error");
    tableEmpty.textContent = "Không thể tải dữ liệu.";
  }
};

const renderTable = () => {
  if (!activeEntity) return;
  const columns = activeEntity.columns || [];
  tableHead.innerHTML = columns.map((col) => `<th>${col.label}</th>`).join("") + "<th>Hành động</th>";
  if (!items.length) {
    tableBody.innerHTML = "";
    tableEmpty.textContent = "Không có bản ghi nào.";
    tableEmpty.style.display = "block";
    return;
  }
  tableEmpty.style.display = "none";
  
  // Kiểm tra xem có đang ở tab Bất động sản không để hiện nút Ảnh
  const isPropertyTab = activeEntity.key === 'properties' || activeEntity.key === 'property' || activeEntity.label.toLowerCase().includes('bất động sản');

  tableBody.innerHTML = items
    .map((item) => {
      const cells = columns
        .map((col) => {
          let value = resolveField(item, col.key);
          if (value === null || value === undefined) {
            value = "—";
          }
          if (col.map && adminMeta.maps && adminMeta.maps[col.map]) {
            value = adminMeta.maps[col.map][String(value)] || value;
          }
          return `<td>${value}</td>`;
        })
        .join("");
        
      // HTML cho nút quản lý ảnh
      const imageBtnHtml = isPropertyTab 
        ? `<button type="button" class="btn btn-sm btn-outline-info me-1" onclick="window.openImagePopup(${item.id})">🖼️ Ảnh</button>` 
        : '';

      return `
        <tr data-id="${item.id}">
          ${cells}
          <td class="text-end" style="white-space:nowrap">
            ${imageBtnHtml}
            <button type="button" class="btn btn-sm btn-outline-primary me-1" data-action="edit" data-id="${item.id}">Sửa</button>
            <button type="button" class="btn btn-sm btn-outline-danger" data-action="delete" data-id="${item.id}">Xóa</button>
          </td>
        </tr>
      `;
    })
    .join("");
};

const resolveField = (item, path) => {
  const keys = path.split(".");
  let value = item;
  for (const key of keys) {
    if (value === null || value === undefined) return null;
    value = value[key];
  }
  return value;
};

const renderFormFields = () => {
  if (!activeEntity) return;
  formFields.innerHTML = "";
  (activeEntity.fields || []).forEach((field) => {
    const wrapper = document.createElement("div");
    wrapper.className = "form-field";
    const label = document.createElement("label");
    label.textContent = field.label;
    let input;
    if (field.type === "textarea") {
      input = document.createElement("textarea");
    } else if (field.type === "select") {
      input = document.createElement("select");
      (field.options || []).forEach((option) => {
        const opt = document.createElement("option");
        opt.value = option.value;
        opt.textContent = option.label;
        input.appendChild(opt);
      });
    } else if (field.type === "checkbox") {
      input = document.createElement("input");
      input.type = "checkbox";
    } else {
      input = document.createElement("input");
      input.type = field.type || "text";
    }
    input.name = field.name;
    if (field.placeholder) input.placeholder = field.placeholder;
    if (field.required) input.required = true;
    if (field.step) input.step = field.step;
    if (field.type !== "checkbox") label.appendChild(input);
    else {
      input.style.marginRight = "8px";
      const container = document.createElement("div");
      container.style.display = "flex";
      container.style.alignItems = "center";
      container.appendChild(input);
      const span = document.createElement("span");
      span.textContent = field.label;
      container.appendChild(span);
      wrapper.appendChild(container);
      formFields.appendChild(wrapper);
      return;
    }
    wrapper.appendChild(label);
    formFields.appendChild(wrapper);
  });
};

const resetForm = (silent = false) => {
  editingId = null;
  form.reset();
  formDeleteBtn.style.display = "none";
  formTitle.textContent = `Tạo mới ${activeEntity?.label || "bản ghi"}`;
  if (!silent) showToast("Đã đặt lại form", "success");
};

const fillForm = (record) => {
  if (!record || !activeEntity) return;
  editingId = record.id;
  formDeleteBtn.style.display = "inline-flex";
  formTitle.textContent = `Cập nhật ${activeEntity.label} #${record.id}`;
  activeEntity.fields.forEach((field) => {
    const input = form.querySelector(`[name="${field.name}"]`);
    if (!input) return;
    const value = record[field.name] !== undefined ? record[field.name] : record[field.name.replace("_id", "")];
    if (field.type === "checkbox") {
      input.checked = Boolean(value);
    } else {
      if (value === null || value === undefined) input.value = "";
      else input.value = value;
    }
  });
};

const serializeForm = () => {
  const data = {};
  activeEntity.fields.forEach((field) => {
    const input = form.querySelector(`[name="${field.name}"]`);
    if (!input) return;
    if (field.type === "checkbox") {
      data[field.name] = input.checked;
    } else {
      data[field.name] = input.value;
    }
  });
  return data;
};

const handleSubmit = async (event) => {
  event.preventDefault();
  if (!activeEntity) return;
  const payload = serializeForm();
  const method = editingId ? "PUT" : "POST";
  const url = editingId ? `${activeEntity.endpoints.detail}${editingId}/` : activeEntity.endpoints.collection;
  try {
    logCsrfState();
    const response = await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-CSRFToken": csrfToken,
      },
      credentials: "same-origin",
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const detail = await extractErrorDetail(response);
      throw new Error(detail);
    }
    await response.json().catch(() => ({}));
    showToast(editingId ? "Đã cập nhật." : "Đã tạo bản ghi.");
    resetForm(true);
    fetchList();
  } catch (error) {
    showToast(error.message, "error");
  }
};

const handleDelete = async () => {
  if (!editingId || !activeEntity) return;
  if (!confirm("Xác nhận xóa bản ghi này?")) return;
  try {
    logCsrfState();
    const response = await fetch(`${activeEntity.endpoints.detail}${editingId}/`, {
      method: "DELETE",
      headers: {
        Accept: "application/json",
        "X-CSRFToken": csrfToken,
      },
      credentials: "same-origin",
    });
    if (!response.ok) {
      const detail = await extractErrorDetail(response);
      throw new Error(detail);
    }
    showToast("Đã xóa.");
    resetForm(true);
    fetchList();
  } catch (error) {
    showToast(error.message, "error");
  }
};

form.addEventListener("submit", handleSubmit);
formResetBtn?.addEventListener("click", (event) => {
  event.preventDefault();
  resetForm(true);
});
formDeleteBtn?.addEventListener("click", (event) => {
  event.preventDefault();
  handleDelete();
});
tableBody.addEventListener("click", (event) => {
  const action = event.target.dataset.action;
  const row = event.target.closest("tr");
  if (!row || !action) return;
  const id = row.dataset.id;
  const record = items.find((item) => item.id === Number(id));
  if (action === "edit") {
    fillForm(record);
  } else if (action === "delete") {
    editingId = Number(id);
    handleDelete();
  }
});

window.openImagePopup = function(propertyId) {
    const url = `/properties/${propertyId}/images/`;
    const popupFeatures = 'width=900,height=750,left=200,top=100,scrollbars=yes,resizable=yes';
    window.open(url, 'ImageManagerPopup', popupFeatures);
};

renderTabs();
switchEntity(activeEntity?.key);