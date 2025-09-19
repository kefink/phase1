(function () {
  function initForm(form) {
    if (!form || form.__autosaveInit) return;
    form.__autosaveInit = true;

    const keyBase =
      form.dataset.autosaveKey || location.pathname + "#" + (form.id || "form");
    const storageKey = "autosave:" + keyBase;

    let dirty = false;
    let draft = {};
    let saveTimer = null;

    const excludedNames = new Set(["csrf_token"]);

    const isSavableField = (el) => {
      if (!el || !el.name) return false;
      if (excludedNames.has(el.name)) return false;
      if (el.matches("[data-no-autosave]")) return false;
      if (el.type === "password" || el.type === "file") return false;
      return true;
    };

    const saveNow = () => {
      try {
        const payload = { ts: Date.now(), data: draft };
        localStorage.setItem(storageKey, JSON.stringify(payload));
      } catch (e) {
        // Swallow quota or serialization errors silently
      }
    };

    const scheduleSave = () => {
      if (saveTimer) clearTimeout(saveTimer);
      saveTimer = setTimeout(saveNow, 500);
    };

    const applyValue = (el, val) => {
      if (!el) return;
      if (el.type === "checkbox") {
        el.checked = !!val;
      } else if (el.type === "radio") {
        const group = form.querySelectorAll(
          `input[type="radio"][name="${el.name}"]`
        );
        group.forEach((r) => (r.checked = r.value === String(val)));
      } else {
        el.value = val;
      }
      // Trigger input/change for any dependent logic
      try {
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
      } catch (e) {}
    };

    const captureField = (t) => {
      if (!isSavableField(t)) return;
      dirty = true;
      if (t.type === "radio") {
        if (t.checked) draft[t.name] = t.value;
      } else if (t.type === "checkbox") {
        draft[t.name] = !!t.checked;
      } else {
        draft[t.name] = t.value;
      }
      scheduleSave();
    };

    form.addEventListener("input", (e) => captureField(e.target));
    form.addEventListener("change", (e) => captureField(e.target));

    // Periodic safeguard autosave
    const interval = setInterval(() => {
      if (dirty) saveNow();
    }, 10000);

    const beforeUnload = (e) => {
      if (dirty) {
        saveNow();
        e.preventDefault();
        e.returnValue = "";
        return "";
      }
    };
    window.addEventListener("beforeunload", beforeUnload);

    form.addEventListener("submit", () => {
      try {
        localStorage.removeItem(storageKey);
      } catch (e) {}
      dirty = false;
      window.removeEventListener("beforeunload", beforeUnload);
      clearInterval(interval);
    });

    // Offer restore if a draft exists
    let stored = null;
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) stored = JSON.parse(raw);
    } catch (e) {}

    if (stored && stored.data && Object.keys(stored.data).length) {
      const banner = document.createElement("div");
      banner.style.cssText =
        "background:#fff8e1;border:1px solid #ffe082;color:#5d4037;padding:10px 12px;border-radius:6px;margin:10px 0;display:flex;justify-content:space-between;align-items:center;gap:8px;";
      const info = document.createElement("div");
      const when = stored.ts ? new Date(stored.ts) : null;
      const whenText = when ? ` from ${when.toLocaleString()}` : "";
      info.textContent = "Unsaved draft found" + whenText + ". Restore it?";
      const actions = document.createElement("div");
      actions.style.cssText = "display:flex;gap:8px;";
      const restoreBtn = document.createElement("button");
      restoreBtn.type = "button";
      restoreBtn.textContent = "Restore";
      restoreBtn.style.cssText =
        "background:#166534;color:#fff;border:none;border-radius:4px;padding:6px 10px;cursor:pointer;";
      const discardBtn = document.createElement("button");
      discardBtn.type = "button";
      discardBtn.textContent = "Discard";
      discardBtn.style.cssText =
        "background:#dc2626;color:#fff;border:none;border-radius:4px;padding:6px 10px;cursor:pointer;";
      actions.appendChild(restoreBtn);
      actions.appendChild(discardBtn);
      banner.appendChild(info);
      banner.appendChild(actions);
      form.insertBefore(banner, form.firstChild);

      restoreBtn.addEventListener("click", () => {
        const data = stored.data;
        for (const name in data) {
          try {
            const selector = `[name="${name.replace(/"/g, '\\"')}"]`;
            const els = form.querySelectorAll(selector);
            if (els && els.length) {
              els.forEach((el) => applyValue(el, data[name]));
            }
          } catch (e) {}
        }
        banner.remove();
      });
      discardBtn.addEventListener("click", () => {
        try {
          localStorage.removeItem(storageKey);
        } catch (e) {}
        banner.remove();
      });
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll('form[data-autosave="true"]').forEach(initForm);
  });
})();
