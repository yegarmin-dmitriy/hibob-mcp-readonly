# HiBob Service User Setup — Instructions for HR Admin

**Purpose:** Create a read-only service user that allows Claude Desktop to query employee data (names, departments, time off, goals). This service user **cannot modify any data** in HiBob.

**Requested by:** Dima Yegarmin (IT)
**Time required:** ~10 minutes

---

## Step 1: Create the Service User

1. Go to **HiBob → Settings → Integrations → Service Users**
2. Click **Create Service User**
3. Set the name: `MCP-Claude-ReadOnly`
4. Click **Save**
5. **Copy both values** and send them to Dima securely (1Password or Slack DM):
   - **Service User ID**
   - **API Token**

> **Important:** The API Token is shown only once. If you lose it, you'll need to generate a new one.

---

## Step 2: Create a Permission Group

1. Go to **HiBob → Settings → Account → Permission Groups**
2. Click **Create Permission Group**
3. Name it: `MCP-Claude-ReadOnly-Group`
4. Add the `MCP-Claude-ReadOnly` service user as the **only member**

---

## Step 3: Configure Data Permissions

In the `MCP-Claude-ReadOnly-Group` permission group, set **People's Data** permissions:

| Category | View | Edit | View History |
|----------|:----:|:----:|:------------:|
| Basic Info (root) | Yes | **No** | No |
| About | **No** | **No** | No |
| Employment | Yes | **No** | Yes |
| Work | Yes | **No** | Yes |
| Lifecycle | Yes | **No** | Yes |
| Personal | **No** | **No** | **No** |
| Identification | **No** | **No** | **No** |
| Home | **No** | **No** | **No** |
| Financial | **No** | **No** | **No** |
| Payroll | **No** | **No** | **No** |

> **Key rule:** Only "Basic Info", "Employment", "Work", and "Lifecycle" should have View access. Everything else must be **No**.

---

## Step 4: Configure Feature Permissions

| Feature | Permission |
|---------|:---------:|
| Time Off — View requests | Yes |
| Time Off — Submit/approve requests | **No** |
| Time Off — Adjust balances | **No** |
| Tasks — View | Yes |
| Tasks — Create/complete | **No** |
| Goals — View | Yes |
| Goals — Create/update/delete | **No** |
| Reports — Run existing reports | Yes |
| Reports — Create/modify reports | **No** |
| People — Add new employees | **No** |

---

## Step 5: Configure Access Rights (whose data is visible)

| Employee Lifecycle Status | Access |
|--------------------------|:------:|
| Employed (active) | Yes |
| Hired (future start date) | Yes |
| On Leave / Parental Leave | Yes |
| Garden Leave | Yes |
| Terminated | **No** |

---

## Verification Checklist

Before sending credentials to Dima, please verify:

- [ ] Service user name is `MCP-Claude-ReadOnly`
- [ ] Permission group has **no Edit permissions** anywhere
- [ ] Personal, Identification, Home, Financial, Payroll categories are all **No**
- [ ] "Add new employees" feature is **No**
- [ ] Terminated employees are **not accessible**
- [ ] Service User ID and API Token have been copied

---

## Questions?

Contact Dima Yegarmin (Slack or email). This is a read-only integration — it cannot change any data in HiBob.
