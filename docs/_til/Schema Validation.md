---
layout: default
title: Schema Validation
comments: true
date: 2024-12-22
categories:
---
# TIL: Constructing and Validating Nested Payloads from DB Config Tables

Constructing deeply nested payloads from database config tables can be tricky, especially when external APIs expect strict schema compliance. Here's how to handle it without losing your mind.

---

## Scenario:
Imagine you have a database table `config_parameters` with fields like:

| id  | category  | key                            | value   |
|-----|-----------|--------------------------------|---------|
| 1   | player    | Max Speed                      | 36      |
| 2   | player    | Stamina                        | 92      |
| 3   | team      | Max Roster Size                | 25      |
| 4   | team      | Home Wins                      | 12      |
| 5   | equipment | Helmet Durability              | 87      |
| 6   | equipment | Ball Pressure                  | 15.5    |

**Goal:**
- Construct a nested payload from this table.
- Validate it against the API's expected schema before sending.

---

## Manual Payload Construction:
A manual, verbose approach often works best for clarity and debugging.

```javascript
let payload = { player: {}, team: {}, equipment: {} };

// Manual assignments
payload.player["Max Speed"] = 36;
payload.player["Stamina"] = 92;
payload.team["Max Roster Size"] = 25;
payload.team["Home Wins"] = 12;
payload.equipment["Helmet Durability"] = 87;
payload.equipment["Ball Pressure"] = 15.5;
```

### Why This Works:
- **Explicit and readable** – No loops to decipher.
- **Manual validation** – Field errors are easy to spot.
- **Patchable** – Missing a value? Add a line.

---

## Automating with Loops (Safely):
Dynamic construction can work with small safeguards in place.

```javascript
let payload = { player: {}, team: {}, equipment: {} };
let dbRows = [
  { category: 'player', key: 'Max Speed', value: 36 },
  { category: 'player', key: 'Stamina', value: 92 },
  { category: 'team', key: 'Max Roster Size', value: 25 },
  { category: 'team', key: 'Home Wins', value: 12 },
  { category: 'equipment', key: 'Helmet Durability', value: 87 },
  { category: 'equipment', key: 'Ball Pressure', value: 15.5 }
];

// Populate payload dynamically
for (let row of dbRows) {
  payload[row.category][row.key] = row.value;
}
```

### Why Be Careful:
- **Unexpected DB values** can break the API.
- **Schema mismatches** happen without notice.

---

## Validating Against API Schema:
Suppose the API expects:

```json
{
  "player": ["Max Speed", "Stamina"],
  "team": ["Max Roster Size"],
  "equipment": ["Helmet Durability", "Ball Pressure"]
}
```

### Validation Example (JS):

```javascript
let apiSchema = {
  player: ["Max Speed", "Stamina"],
  team: ["Max Roster Size"],
  equipment: ["Helmet Durability", "Ball Pressure"]
};

function validatePayload(payload, schema) {
  let errors = [];

  for (let category in schema) {
    schema[category].forEach(key => {
      if (!(key in payload[category])) {
        errors.push(`${category}: Missing ${key}`);
      }
    });
  }

  return errors.length ? errors : "Payload is valid!";
}

console.log(validatePayload(payload, apiSchema));
```

---

## Real-Life Example – Sports Config:

```javascript
let gamePayload = { player: {}, team: {}, equipment: {} };

gamePayload.player["Max Speed"] = 36;
gamePayload.player["Stamina"] = 92;
gamePayload.team["Max Roster Size"] = 25;
gamePayload.team["Home Wins"] = 12;
gamePayload.equipment["Helmet Durability"] = 87;
gamePayload.equipment["Ball Pressure"] = 15.5;
```

### Validate Sports Payload:

```javascript
let sportsSchema = {
  player: ["Max Speed", "Stamina"],
  team: ["Max Roster Size"],
  equipment: ["Helmet Durability", "Ball Pressure"]
};
console.log(validatePayload(gamePayload, sportsSchema));
```

---

## TL;DR:
- Building payloads manually avoids unnecessary complexity.
- Explicit assignments are easy to validate.
- Schema validation catches mismatches early.

