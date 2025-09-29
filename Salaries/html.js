export default defineComponent({
  name: "Generate HTML Card",
  description: "Builds an HTML salary card from analysis and form data provided by previous steps.",
  type: "action",
  props: {
    analyze_salary: {
      type: "object",
      label: "Salary Analysis",
      description: "Data from the analyze_salary step, e.g. { score, rationale }",
    },
    form_data: {
      type: "object",
      label: "Form Data",
      description: "Parsed form data from the code step, e.g. { ruolo, localita, stipendio }",
    },
  },
  methods: {
    escapeHtml(s) {
      return String(s || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    },
  },
  async run({ $ }) {
    const analysis = this.analyze_salary || {};
    const form = this.form_data || {};

    const score = Number(analysis.score ?? 2);
    const rationale = analysis.rationale ?? "";

    const ruolo =
      form.ruolo ??
      form.role ??
      form.titolo ??
      "—";

    const localita =
      form.localita ??
      form.location ??
      form.citta ??
      "—";

    const stipendioRaw =
      form.stipendio ??
      form.salary ??
      form.compenso ??
      form.stipendio_annuo ??
      0;

    const stipendio = Number(stipendioRaw) || 0;

    const labels = {
      1: "Sopra la media",
      2: "In media",
      3: "Sotto la media",
      4: "Sotto la media (Milano)",
    };
    const label = labels[score] ?? "Valutazione stipendio";

    const html = [
      "<!doctype html>",
      "<html>",
      "<head>",
      '<meta charset="utf-8">',
      "<title>Valutazione</title>",
      "</head>",
      "<body>",
      `<h1>${this.escapeHtml(ruolo)} · ${this.escapeHtml(localita)} · €${stipendio.toLocaleString("it-IT")}</h1>`,
      `<div>${this.escapeHtml(label)}</div>`,
      `<p>${this.escapeHtml(rationale)}</p>`,
      "</body>",
      "</html>",
    ].join("");

    $.export("$summary", "Generated salary evaluation HTML card");

    return {
      ok: true,
      html,
      data: {
        score,
        rationale,
        ruolo,
        localita,
        stipendio,
      },
    };
  },
});