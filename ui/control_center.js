const riskApi = "http://127.0.0.1:8010";
const priorityApi = "http://127.0.0.1:8020";

const riskForm = document.getElementById("riskForm");
const priorityForm = document.getElementById("priorityForm");
const riskOutput = document.getElementById("riskOutput");
const priorityOutput = document.getElementById("priorityOutput");
const policyTarget = document.getElementById("policyTarget");
const policyEditor = document.getElementById("policyEditor");
const policyOutput = document.getElementById("policyOutput");
const policyAEditor = document.getElementById("policyAEditor");
const policyBEditor = document.getElementById("policyBEditor");
const compareOutput = document.getElementById("compareOutput");
const historyOutput = document.getElementById("historyOutput");

function pretty(value) {
  return JSON.stringify(value, null, 2);
}

function apiBase(target) {
  return target === "risk" ? riskApi : priorityApi;
}

function comparisonRequisitions() {
  return [
    {
      requisition_id: "CMP-1001",
      requester_department: "Emergency",
      amount: 15000,
      hours_to_stockout: 5,
      vulnerability_index: 0.8,
      compliance_blocked: false,
    },
    {
      requisition_id: "CMP-1002",
      requester_department: "ICU",
      amount: 42000,
      hours_to_stockout: 12,
      vulnerability_index: 0.7,
      compliance_blocked: false,
    },
    {
      requisition_id: "CMP-1003",
      requester_department: "Field Ops",
      amount: 9000,
      hours_to_stockout: 20,
      vulnerability_index: 0.5,
      compliance_blocked: true,
    },
  ];
}

async function refreshMetrics() {
  try {
    const [riskRes, priorityRes] = await Promise.all([
      fetch(`${riskApi}/metrics`).then((r) => r.json()),
      fetch(`${priorityApi}/metrics`).then((r) => r.json()),
    ]);

    document.getElementById("kpiEvaluations").textContent = riskRes.metrics.evaluations_total;
    document.getElementById("kpiHuman").textContent = riskRes.metrics.human_review;
    document.getElementById("kpiPrioritizations").textContent = priorityRes.metrics.prioritizations_total;
    document.getElementById("kpiItems").textContent = priorityRes.metrics.items_processed;
  } catch (error) {
    document.getElementById("kpiEvaluations").textContent = "-";
    document.getElementById("kpiHuman").textContent = "-";
    document.getElementById("kpiPrioritizations").textContent = "-";
    document.getElementById("kpiItems").textContent = "-";
  }
}

async function loadPolicyIntoEditor(target = policyTarget.value) {
  try {
    const response = await fetch(`${apiBase(target)}/policy`);
    const body = await response.json();
    policyEditor.value = pretty(body);
    policyOutput.textContent = `Loaded ${target} policy: ${body.policy_version || "unknown"}`;

    if (target === "priority") {
      policyAEditor.value = pretty(body);
      if (!policyBEditor.value.trim()) {
        const policyB = structuredClone(body);
        policyB.policy_version = `${policyB.policy_version || "policy"}-variant`;
        if (policyB.weights && policyB.weights.vulnerability_boost !== undefined) {
          policyB.weights.vulnerability_boost = Number((policyB.weights.vulnerability_boost + 0.1).toFixed(2));
        }
        policyBEditor.value = pretty(policyB);
      }
    }
  } catch (error) {
    policyOutput.textContent = `Failed to load policy: ${error.message}`;
  }
}

async function validatePolicy() {
  try {
    const parsed = JSON.parse(policyEditor.value);
    const response = await fetch(`${apiBase(policyTarget.value)}/policy/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ policy: parsed }),
    });
    const body = await response.json();
    policyOutput.textContent = pretty(body);
  } catch (error) {
    policyOutput.textContent = `Invalid JSON or request failure: ${error.message}`;
  }
}

async function applyPolicy() {
  try {
    const parsed = JSON.parse(policyEditor.value);
    const validateResponse = await fetch(`${apiBase(policyTarget.value)}/policy/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ policy: parsed }),
    });
    const validateBody = await validateResponse.json();

    if (!validateBody.valid) {
      policyOutput.textContent = pretty({
        applied: false,
        reason: "Validation failed. Fix policy before apply.",
        details: validateBody,
      });
      return;
    }

    const response = await fetch(`${apiBase(policyTarget.value)}/policy/apply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ policy: parsed }),
    });
    const body = await response.json();
    policyOutput.textContent = pretty(body);
  } catch (error) {
    policyOutput.textContent = `Invalid JSON or request failure: ${error.message}`;
  }
}

async function runComparison() {
  try {
    const policyA = JSON.parse(policyAEditor.value);
    const policyB = JSON.parse(policyBEditor.value);
    compareOutput.textContent = "Comparing policy packs...";

    const response = await fetch(`${priorityApi}/compare/policies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        requisitions: comparisonRequisitions(),
        policy_a: policyA,
        policy_b: policyB,
      }),
    });
    const body = await response.json();
    compareOutput.textContent = pretty(body);
  } catch (error) {
    compareOutput.textContent = `Comparison failed: ${error.message}`;
  }
}

async function refreshHistory() {
  try {
    const [riskHistory, priorityHistory] = await Promise.all([
      fetch(`${riskApi}/history?limit=8`).then((r) => r.json()),
      fetch(`${priorityApi}/history?limit=8`).then((r) => r.json()),
    ]);

    historyOutput.textContent = pretty({
      risk_timeline: riskHistory.timeline || [],
      prioritization_timeline: priorityHistory.timeline || [],
    });
  } catch (error) {
    historyOutput.textContent = `Could not load timeline: ${error.message}`;
  }
}

riskForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(riskForm);

  const payload = {
    order_id: formData.get("order_id"),
    customer_tier: formData.get("customer_tier"),
    category: formData.get("category"),
    discount_percent: Number(formData.get("discount_percent")),
    line_items: [
      {
        sku: "CORE-SKU",
        quantity: 3,
        unit_price: 180,
        expected_price: 130,
      },
    ],
  };

  riskOutput.textContent = "Evaluating...";

  try {
    const response = await fetch(`${riskApi}/evaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await response.json();
    riskOutput.textContent = pretty(body);
  } catch (error) {
    riskOutput.textContent = `Request failed: ${error.message}`;
  }

  refreshMetrics();
});

priorityForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(priorityForm);

  const payload = {
    requisitions: [
      {
        requisition_id: formData.get("requisition_id"),
        requester_department: formData.get("requester_department"),
        amount: Number(formData.get("amount")),
        hours_to_stockout: Number(formData.get("hours_to_stockout")),
        vulnerability_index: Number(formData.get("vulnerability_index")),
        compliance_blocked: formData.get("compliance_blocked") === "on",
      },
    ],
  };

  priorityOutput.textContent = "Prioritizing...";

  try {
    const response = await fetch(`${priorityApi}/prioritize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await response.json();
    priorityOutput.textContent = pretty(body);
  } catch (error) {
    priorityOutput.textContent = `Request failed: ${error.message}`;
  }

  refreshMetrics();
});

document.querySelectorAll(".pill").forEach((button) => {
  button.addEventListener("click", async () => {
    const scenario = button.dataset.scenario;

    if (scenario === "surge") {
      priorityOutput.textContent = "Running surge simulation...";
      const response = await fetch(`${priorityApi}/simulate/surge`, { method: "POST" });
      const body = await response.json();
      priorityOutput.textContent = pretty(body);
      refreshMetrics();
      return;
    }

    if (scenario === "balanced") {
      priorityForm.requisition_id.value = "REQ-5200";
      priorityForm.requester_department.value = "Field Ops";
      priorityForm.amount.value = "18000";
      priorityForm.hours_to_stockout.value = "15";
      priorityForm.vulnerability_index.value = "0.4";
      priorityForm.compliance_blocked.checked = false;
    }

    if (scenario === "compliance") {
      priorityForm.requisition_id.value = "REQ-5300";
      priorityForm.requester_department.value = "Surgery";
      priorityForm.amount.value = "9500";
      priorityForm.hours_to_stockout.value = "12";
      priorityForm.vulnerability_index.value = "0.5";
      priorityForm.compliance_blocked.checked = true;
    }
  });
});

document.getElementById("refreshMetrics").addEventListener("click", refreshMetrics);
document.getElementById("loadPolicyBtn").addEventListener("click", () => loadPolicyIntoEditor());
document.getElementById("validatePolicyBtn").addEventListener("click", validatePolicy);
document.getElementById("applyPolicyBtn").addEventListener("click", applyPolicy);
document.getElementById("comparePoliciesBtn").addEventListener("click", runComparison);
document.getElementById("refreshHistoryBtn").addEventListener("click", refreshHistory);

policyTarget.addEventListener("change", () => loadPolicyIntoEditor(policyTarget.value));

refreshMetrics();
loadPolicyIntoEditor();
refreshHistory();
