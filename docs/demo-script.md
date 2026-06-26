# AgentForge Studio v2 Demo Script

This script demonstrates the implemented local workflow. It avoids claims about unimplemented SaaS/multi-tenant features.

## 1. Start the stack

```bash
cp .env.example .env
docker compose up --build
```

Open `http://localhost:3000`.

## 2. Choose Customer Feedback Intelligence Team

Open **Templates**, choose **Customer Feedback Intelligence Team**, and inspect its Agent Pack YAML.

## 3. Upload sample CSV

Open **Memory**, upload `sample_data/customer_feedback.csv`, then click **Index**. The current memory engine chunks text and performs keyword search.

## 4. Run workflow

Open **Run Console** and run:

```text
Analyze customer feedback, group major complaints, classify severity, and generate an executive report.
```

Expected flow:

```text
Planner → Data Cleaner → Feedback Analyst → Bug Classifier → Executive Summary Writer
```

## 5. Watch traces

Open **Trace Viewer**. Confirm that agent steps, tool calls, policy checks, and final output are persisted.

## 6. Inspect policy behavior

Run the Sales Outreach pack. The `email_draft` tool can trigger the approval flow depending on tool permissions and pack policy. Open **Approvals** to approve, edit-and-approve, or reject.

## 7. Run evaluation

Open **Evaluation Lab**, select the Customer Feedback pack, click **Run evaluation**, then export the Markdown report.

## 8. Export/edit pack YAML

Open **Agent Packs**, choose a pack, edit Overview/Agents/YAML, validate, then save a new version.
