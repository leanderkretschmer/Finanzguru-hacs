/* eslint-disable no-undef */

const DEFAULTS = {
  month: {
    expenses_entity: "",
    income_entity: "",
    title: "Finanzguru: Monat",
  },
  today: {
    entity: "",
    title: "Finanzguru: Heute",
  },
  contracts: {
    entity: "",
    title: "Finanzguru: Verträge",
  },
  budget: {
    entity: "",
    title: "Finanzguru: Budget",
  },
};

function fireEvent(node, type, detail = {}, options = {}) {
  const event = new Event(type, {
    bubbles: options.bubbles ?? true,
    cancelable: options.cancelable ?? false,
    composed: options.composed ?? true,
  });
  event.detail = detail;
  node.dispatchEvent(event);
  return event;
}

function createHaCard(title) {
  const card = document.createElement("ha-card");
  if (title) {
    const header = document.createElement("div");
    header.className = "card-header";
    header.textContent = title;
    card.appendChild(header);
  }
  return card;
}

class FinanzguruBaseCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (this.isConnected) this._render();
  }

  get hass() {
    return this._hass;
  }

  setConfig(config) {
    this._config = config;
    this._render();
  }

  getCardSize() {
    return 3;
  }

  _renderRow(label, value) {
    const row = document.createElement("div");
    row.className = "fg-row";

    const l = document.createElement("div");
    l.className = "fg-label";
    l.textContent = label;

    const v = document.createElement("div");
    v.className = "fg-value";
    v.textContent = value ?? "—";

    row.appendChild(l);
    row.appendChild(v);
    return row;
  }

  _applyStyles(root) {
    const style = document.createElement("style");
    style.textContent = `
      .fg-wrap { padding: 16px; }
      .fg-row { display: flex; justify-content: space-between; gap: 12px; padding: 6px 0; }
      .fg-label { opacity: 0.8; }
      .fg-value { font-variant-numeric: tabular-nums; }
      .fg-list { margin-top: 8px; display: grid; gap: 6px; }
      .fg-item { display: flex; justify-content: space-between; gap: 12px; }
      .fg-muted { opacity: 0.7; font-size: 0.9em; }
    `;
    root.appendChild(style);
  }

  _render() {}
}

class FinanzguruMonthCard extends FinanzguruBaseCard {
  static getStubConfig() {
    return { type: "custom:finanzguru-month-card", ...DEFAULTS.month };
  }

  _render() {
    if (!this._config) return;
    const root = this.shadowRoot ?? this.attachShadow({ mode: "open" });
    root.innerHTML = "";
    this._applyStyles(root);

    const card = createHaCard(this._config.title);
    const wrap = document.createElement("div");
    wrap.className = "fg-wrap";

    const expenses = this._getState(this._config.expenses_entity);
    const income = this._getState(this._config.income_entity);
    wrap.appendChild(this._renderRow("Ausgaben", expenses?.state));
    wrap.appendChild(this._renderRow("Einnahmen", income?.state));

    const categories = expenses?.attributes?.kategorien ?? income?.attributes?.kategorien;
    if (categories) {
      const pre = document.createElement("pre");
      pre.className = "fg-muted";
      pre.style.whiteSpace = "pre-wrap";
      pre.textContent = JSON.stringify(categories, null, 2);
      wrap.appendChild(pre);
    } else {
      const hint = document.createElement("div");
      hint.className = "fg-muted";
      hint.textContent = "Kategorien sind nicht verfügbar (API liefert keine Daten).";
      wrap.appendChild(hint);
    }

    card.appendChild(wrap);
    root.appendChild(card);
  }

  _getState(entityId) {
    if (!entityId || !this._hass) return null;
    return this._hass.states[entityId] ?? null;
  }
}

class FinanzguruTodayCard extends FinanzguruBaseCard {
  static getStubConfig() {
    return { type: "custom:finanzguru-today-card", ...DEFAULTS.today };
  }

  _render() {
    if (!this._config) return;
    const root = this.shadowRoot ?? this.attachShadow({ mode: "open" });
    root.innerHTML = "";
    this._applyStyles(root);

    const card = createHaCard(this._config.title);
    const wrap = document.createElement("div");
    wrap.className = "fg-wrap";
    const stateObj = this._getState(this._config.entity);
    wrap.appendChild(this._renderRow("Heute", stateObj?.state));
    card.appendChild(wrap);
    root.appendChild(card);
  }

  _getState(entityId) {
    if (!entityId || !this._hass) return null;
    return this._hass.states[entityId] ?? null;
  }
}

class FinanzguruContractsCard extends FinanzguruBaseCard {
  static getStubConfig() {
    return { type: "custom:finanzguru-contracts-card", ...DEFAULTS.contracts };
  }

  _render() {
    if (!this._config) return;
    const root = this.shadowRoot ?? this.attachShadow({ mode: "open" });
    root.innerHTML = "";
    this._applyStyles(root);

    const card = createHaCard(this._config.title);
    const wrap = document.createElement("div");
    wrap.className = "fg-wrap";
    const stateObj = this._getState(this._config.entity);
    wrap.appendChild(this._renderRow("Anzahl", stateObj?.state));

    const list = stateObj?.attributes?.list;
    if (Array.isArray(list) && list.length) {
      const grid = document.createElement("div");
      grid.className = "fg-list";
      list.slice(0, 20).forEach((it) => {
        const row = document.createElement("div");
        row.className = "fg-item";
        const name = document.createElement("div");
        name.textContent = it?.name ?? "—";
        const price = document.createElement("div");
        const rate = it?.payment_rate ? ` / ${it.payment_rate}` : "";
        const currency = it?.currency ? ` ${it.currency}` : "";
        price.textContent = `${it?.price ?? "—"}${currency}${rate}`;
        row.appendChild(name);
        row.appendChild(price);
        grid.appendChild(row);
      });
      wrap.appendChild(grid);
    }

    card.appendChild(wrap);
    root.appendChild(card);
  }

  _getState(entityId) {
    if (!entityId || !this._hass) return null;
    return this._hass.states[entityId] ?? null;
  }
}

class FinanzguruBudgetCard extends FinanzguruBaseCard {
  static getStubConfig() {
    return { type: "custom:finanzguru-budget-card", ...DEFAULTS.budget };
  }

  _render() {
    if (!this._config) return;
    const root = this.shadowRoot ?? this.attachShadow({ mode: "open" });
    root.innerHTML = "";
    this._applyStyles(root);

    const card = createHaCard(this._config.title);
    const wrap = document.createElement("div");
    wrap.className = "fg-wrap";
    const stateObj = this._getState(this._config.entity);
    wrap.appendChild(this._renderRow("Auslastung", stateObj?.state ? `${stateObj.state}%` : "—"));
    card.appendChild(wrap);
    root.appendChild(card);
  }

  _getState(entityId) {
    if (!entityId || !this._hass) return null;
    return this._hass.states[entityId] ?? null;
  }
}

class FinanzguruEntityEditor extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (this.isConnected) this._render();
  }

  setConfig(config) {
    this._config = config;
    this._render();
  }

  _render() {
    const root = this.shadowRoot ?? this.attachShadow({ mode: "open" });
    root.innerHTML = `
      <style>
        .fg-form { padding: 12px 16px 4px; display: grid; gap: 12px; }
      </style>
      <div class="fg-form">
        <ha-textfield label="Titel" value="${this._config?.title ?? ""}"></ha-textfield>
        <ha-entity-picker></ha-entity-picker>
      </div>
    `;

    const titleField = root.querySelector("ha-textfield");
    titleField.addEventListener("input", (ev) => {
      const value = ev.target.value;
      this._config = { ...this._config, title: value };
      fireEvent(this, "config-changed", { config: this._config });
    });

    const picker = root.querySelector("ha-entity-picker");
    picker.hass = this._hass;
    picker.value = this._config?.entity ?? "";
    picker.addEventListener("value-changed", (ev) => {
      const value = ev.detail.value;
      this._config = { ...this._config, entity: value };
      fireEvent(this, "config-changed", { config: this._config });
    });
  }
}

class FinanzguruMonthEditor extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (this.isConnected) this._render();
  }

  setConfig(config) {
    this._config = config;
    this._render();
  }

  _render() {
    const root = this.shadowRoot ?? this.attachShadow({ mode: "open" });
    root.innerHTML = `
      <style>
        .fg-form { padding: 12px 16px 4px; display: grid; gap: 12px; }
      </style>
      <div class="fg-form">
        <ha-textfield label="Titel" value="${this._config?.title ?? ""}"></ha-textfield>
        <ha-entity-picker id="expenses" label="Ausgaben Sensor"></ha-entity-picker>
        <ha-entity-picker id="income" label="Einnahmen Sensor"></ha-entity-picker>
      </div>
    `;

    const titleField = root.querySelector("ha-textfield");
    titleField.addEventListener("input", (ev) => {
      const value = ev.target.value;
      this._config = { ...this._config, title: value };
      fireEvent(this, "config-changed", { config: this._config });
    });

    const ex = root.querySelector("#expenses");
    ex.hass = this._hass;
    ex.value = this._config?.expenses_entity ?? "";
    ex.addEventListener("value-changed", (ev) => {
      this._config = { ...this._config, expenses_entity: ev.detail.value };
      fireEvent(this, "config-changed", { config: this._config });
    });

    const inc = root.querySelector("#income");
    inc.hass = this._hass;
    inc.value = this._config?.income_entity ?? "";
    inc.addEventListener("value-changed", (ev) => {
      this._config = { ...this._config, income_entity: ev.detail.value };
      fireEvent(this, "config-changed", { config: this._config });
    });
  }
}

customElements.define("finanzguru-month-card", FinanzguruMonthCard);
customElements.define("finanzguru-today-card", FinanzguruTodayCard);
customElements.define("finanzguru-contracts-card", FinanzguruContractsCard);
customElements.define("finanzguru-budget-card", FinanzguruBudgetCard);
customElements.define("finanzguru-entity-editor", FinanzguruEntityEditor);
customElements.define("finanzguru-month-editor", FinanzguruMonthEditor);

window.customCards = window.customCards || [];
window.customCards.push(
  {
    type: "finanzguru-month-card",
    name: "Finanzguru: Monat",
    description: "Monatliche Ausgaben/Einnahmen inkl. Kategorien.",
  },
  {
    type: "finanzguru-today-card",
    name: "Finanzguru: Heute",
    description: "Heutige Ausgaben.",
  },
  {
    type: "finanzguru-contracts-card",
    name: "Finanzguru: Verträge",
    description: "Vertragsübersicht inkl. Liste.",
  },
  {
    type: "finanzguru-budget-card",
    name: "Finanzguru: Budget",
    description: "Budget-Auslastung (falls verfügbar).",
  }
);

FinanzguruMonthCard.getConfigElement = () => document.createElement("finanzguru-month-editor");
FinanzguruTodayCard.getConfigElement = () => document.createElement("finanzguru-entity-editor");
FinanzguruContractsCard.getConfigElement = () => document.createElement("finanzguru-entity-editor");
FinanzguruBudgetCard.getConfigElement = () => document.createElement("finanzguru-entity-editor");

