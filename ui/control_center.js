const riskApi = "http://127.0.0.1:8010";
const priorityApi = "http://127.0.0.1:8020";

const riskForm = document.getElementById("riskForm");
const priorityForm = document.getElementById("priorityForm");
const riskOutput = document.getElementById("riskOutput");
const priorityOutput = document.getElementById("priorityOutput");

function pretty(value) {
  return JSON.stringify(value, null, 2);
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

refreshMetrics();
