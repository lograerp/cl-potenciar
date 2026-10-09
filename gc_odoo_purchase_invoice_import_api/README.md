# GC Odoo Purchase Invoice Import API

Módulo Odoo 16.0 que expone un endpoint para que el integrador **Radiant /
"Looking for Trouble"** envíe facturas de compra ya mapeadas a IDs de Odoo
(contrato v0.1) y el sistema cree la factura de proveedor **en borrador**.

- Versión: `16.0.2.0.0`
- Dependencias: `base`, `account`, `analytic`, `l10n_ar`.

## Por qué un módulo nuevo e independiente

Se creó como módulo nuevo, sin depender de `gc_odoo_potenciar_api`: al momento
de crearlo ese módulo tenía trabajo en curso de otra persona que no debía
tocarse. No hay ninguna dependencia en tiempo de ejecución entre ambos; el
módulo existente solo se usó como referencia de patrón.

## Endpoint

```
POST /api/v1/purchase-invoices
Content-Type: application/json
```

Es la **única** ruta de escritura. Solo acepta `POST` (con `GET`/`PUT` Odoo
responde `405`). La barra final (`/api/v1/purchase-invoices/`) también se
acepta.

URLs por entorno:

| Entorno | URL |
|---|---|
| Dev (dominio) | `https://dev.potenciar.lograerp.com/api/v1/purchase-invoices` |
| Dev (host, contenedor `potenciar_dev-odoo-1`) | `http://localhost:8138/api/v1/purchase-invoices` |
| Dentro del contenedor | `http://localhost:8069/api/v1/purchase-invoices` |

> **404:** la ruta **no** es `/api/v1/purchase-invoices/import` ni ninguna
> otra variante. Un `404` indica un path mal escrito (o que el módulo no está
> instalado en la base). Si el módulo está bien instalado, un request sin
> credenciales a la ruta correcta devuelve `401`, no `404`.

### Documentación interactiva (Swagger)

```
GET /api/v1/purchase-invoices/docs           # Swagger UI
GET /api/v1/purchase-invoices/openapi.json   # Especificación OpenAPI 3.0
```

Ambas son públicas (sin autenticación). Ojo con el `.json`:
`/api/v1/purchase-invoices/openapi` (sin extensión) devuelve `404`.

### Autenticación

HTTP Basic Auth con **las mismas credenciales que un usuario usa para entrar
al backend de Odoo** (`res.users.authenticate`, la misma validación que usa
el login web) — no hay token ni secreto separado que generar o rotar.

```
Authorization: Basic base64(usuario:contraseña)
```

Importante sobre permisos: el usuario solo se usa para **autenticar**. Toda
la creación (log, contacto, factura, adjunto) se ejecuta con `sudo()`, así
que los grupos/permisos del usuario **no** limitan lo que puede crear:
cualquier usuario activo con contraseña válida puede importar facturas.

**Recomendación de despliegue** (no impuesta por el módulo): crear un
usuario de servicio dedicado (ej. `servicio_proveedor`) y no reusar la
contraseña de un usuario humano. Usar siempre HTTPS: Basic Auth manda la
contraseña en cada request (el dominio de dev redirige `http` → `https` con
`301`; algunos clientes convierten el `POST` en `GET` al seguir la
redirección, así que conviene usar `https` directo).

## Contrato de entrada (v0.1)

El proveedor manda la factura **ya mapeada** a IDs de Odoo (`partner_id`,
`product_id`, `account_id`, `tax_ids`, `uom_id`, `analytic_distribution`,
`journal_id`, `company_id`, `document_type_id`, `currency_id`, bajo la clave
`odoo` de cada bloque). Esta API **confía en esos IDs tal cual**: solo
verifica que cada uno EXISTA (`browse().exists()`), nunca los resuelve ni
corrige por su cuenta. Ver DECISIONES.md para el detalle y el riesgo
aceptado de esta decisión.

```json
{
  "schema_version": "0.1",
  "source": {
    "system": "radiant", "tenant_id": "<uuid tenant>", "invoice_id": "<uuid factura>",
    "idempotency_key": "33718285289-1-00002-00000018", "sent_at": "2026-06-23T14:05:00-03:00"
  },
  "target": {
    "company_id": 1, "journal_id": 12, "move_type": "in_invoice",
    "final_state": "draft", "final_state_reason": "tenant_config_always_draft"
  },
  "partner": {
    "cuit": "33718285289", "name": "WFLUCAR", "vat_condition": "IVA Responsable Inscripto",
    "address": "Belgrano 525", "city": "Canals", "province": "X", "postal_code": "2650",
    "odoo": {
      "partner_id": 581, "resolution": "matched", "policy_if_missing": "review",
      "afip_responsibility_code": "1", "identification_type": "CUIT", "state_id": 7
    }
  },
  "document": {
    "point_of_sale": 2, "invoice_number": 18, "invoice_date": "2026-06-23", "due_date": "2026-06-23",
    "cae": "86251025478576", "cae_due_date": "2026-07-03",
    "odoo": {
      "document_type_id": 1, "document_number": "00002-00000018",
      "accounting_date": "2026-06-23", "currency_id": 19,
      "narration": "CAE 86251025478576 (vto. 2026-07-03) · Radiant <uuid factura>"
    }
  },
  "lines": [{
    "sequence": 1, "product_code": "00001", "description": "SERVICIOS DE CONSULTORIA EXTERNA",
    "quantity": 1, "unit_price": 13130706.60, "subtotal": 13130706.60, "vat_rate": 21,
    "odoo": {
      "product_id": 345, "account_id": 210, "tax_ids": [7], "uom_id": 1,
      "analytic_distribution": {"33": 100}
    }
  }],
  "taxes": {"vat": [{"rate": 21, "base": 13130706.60, "amount": 2757448.39, "odoo_tax_id": 7}],
            "perceptions": [], "internal_taxes_amount": 0, "exempt_amount": 0, "non_taxed_amount": 0},
  "totals": {"net_amount": 13130706.60, "vat_amount": 2757448.39, "perceptions_amount": 0,
             "internal_taxes_amount": 0, "total_amount": 15888154.99},
  "validation": {"tolerance": 1.00, "action_if_exceeded": "observation"},
  "attachment": {"file_name": "33718285289_0002FCA00000018.pdf", "mime_type": "application/pdf",
                 "content_base64": "<PDF en base64>"}
}
```

Ver el ejemplo completo en `tests/fixtures/valid_v01_single_line.json` y el
detalle campo por campo en `static/openapi.json`.

### Campos obligatorios

Validados en `services/payload_validator.py`; si falta alguno responde `400`
con el path del campo en `details`:

- `schema_version` = `"0.1"` (exacto).
- Objetos `source`, `target`, `partner`, `document`, `totals` y arreglo
  `lines` no vacío.
- `source.idempotency_key`.
- `target.company_id`, `target.journal_id`, `target.move_type`
  (`in_invoice` o `in_refund`).
- `partner.cuit`.
- `document.invoice_date` (formato `YYYY-MM-DD`; `due_date` opcional, mismo
  formato).
- `document.odoo.document_type_id`.
- `document.odoo.document_number` **o** el par `document.point_of_sale` +
  `document.invoice_number` (se arma como `PPPPP-NNNNNNNN`).
- Por línea: `quantity`, `unit_price` (numéricos), `description`, y al menos
  uno de `odoo.product_id` / `odoo.account_id`.
- `totals.net_amount`, `totals.vat_amount`, `totals.total_amount` (numéricos).

### IDs de Odoo verificados

Antes de crear nada se verifica que existan (`400` si alguno no existe):
`target.company_id`, `target.journal_id`, `document.odoo.document_type_id`,
`document.odoo.currency_id`, `partner.odoo.partner_id`, y por línea
`product_id`, `account_id`, cada `tax_ids[]`, `uom_id` y cada cuenta de
`analytic_distribution`. `partner.odoo.state_id` **no** se verifica: si no
existe, simplemente no se usa al crear el contacto.

### Estado final

La factura se crea **siempre en borrador**. Si `target.final_state` viene con
otro valor, se ignora y se agrega un warning.

### Duplicados

Regla: mismo contacto comercial (`commercial_partner_id`) + `move_type` +
tipo de documento + número de documento (`l10n_latam_document_number`),
excluyendo facturas canceladas. **No** se usa `source.idempotency_key` ni
`source.invoice_id` para detectar duplicados: solo se guardan como
trazabilidad (en el log y en la factura, campos
`gc_import_source_invoice_id` / `gc_import_idempotency_key`). Si hay
duplicado responde `200` con `status: "duplicate"` y el `move_id` de la
factura existente.

### Partner ausente

Si `partner.odoo.partner_id` no viene informado, se usa
`partner.odoo.policy_if_missing`:

- `"create"`: busca por CUIT normalizado entre **todos** los contactos con
  CUIT cargado (sin filtrar por proveedor); si no hay match, **crea el
  contacto** (`res.partner`, empresa, país Argentina, tipo de identificación
  CUIT, `supplier_rank=1`) desde los datos del bloque `partner`
  (`name`, `address`, `city`, `postal_code`, `odoo.state_id`,
  `odoo.afip_responsibility_code`). Se agrega un warning
  `"Contacto creado: ..."`.
- cualquier otro valor (incluido `"review"` o ausente): **no crea nada**,
  responde `422 pending_review`.

### Validación de montos

Nunca se confía en `validation.checks` del payload (se guarda en el log solo
como información). Esta API recalcula sus propios chequeos con la tolerancia
de `validation.tolerance` (o el parámetro de configuración si no viene):

| `code` | Esperado | Real |
|---|---|---|
| `lines_vs_net` | `totals.net_amount` | Σ `quantity * unit_price` |
| `line_subtotal[i]` | `quantity * unit_price` | `subtotal` de la línea (solo si viene) |
| `vat_total` | `totals.vat_amount` | Σ `taxes.vat[].amount` |
| `total` | `totals.total_amount` | `net + vat + perceptions + internal_taxes` (de `totals`) `+ exempt + non_taxed` (de `taxes`) |
| `odoo_total` | `totals.total_amount` | `move.amount_total` (post-creación) |

Comportamiento según la diferencia:

- **Diferencia = 0**: sin nota.
- **Diferencia > 0 y dentro de tolerancia**: se crea igual, pero se agrega un
  warning y el log queda con `has_observations=true`.
- **Diferencia > tolerancia**: decide `validation.action_if_exceeded`:
  `"observation"` (default) crea igual con warning y `has_observations=true`;
  `"reject"` responde `400` sin crear nada. Si el que falla es `odoo_total`,
  la factura ya creada se revierte (savepoint) y no queda nada en Odoo.

### Adjunto PDF

Si `attachment.content_base64` viene informado, se valida que decodifique
como Base64 válido y que sea un PDF real (`mime_type == "application/pdf"` +
magic bytes `%PDF`). Se crea un `ir.attachment` vinculado a la factura y se
setea como `message_main_attachment_id`. El base64 **nunca** se guarda en el
log crudo (`raw_payload`): se redacta a `"<omitted N bytes>"`.

### Contrato de salida

Para todas las respuestas que pasan la autenticación: `success`, `status`,
`document_id`, `idempotency_key`, `warnings`, `details`, `checks` siempre
presentes. `success` es `true` solo si `status == "created"`. `document_id`
es `source.invoice_id` del payload (puede ser `null`). `warnings`, `details`
y `checks` son siempre listas (vacías si no aplica). `message`, `move_id`,
`move_name` y `log_id` aparecen cuando aplican.

**201 — creada en borrador**
```json
{
  "success": true, "status": "created",
  "document_id": "b6f6c1d2-1e3a-4a3f-9c1e-000000000002",
  "idempotency_key": "33718285289-1-00002-00000018",
  "message": "Factura FA-A 00002-00000018 creada en borrador.",
  "move_id": 123, "move_name": "FA-A 00002-00000018", "log_id": 45,
  "warnings": [], "details": [],
  "checks": [{"code": "total", "expected": 15888154.99, "actual": 15888154.99, "diff": 0, "passed": true}]
}
```

**200 — duplicado** (idempotente, no es error técnico) — misma forma, `status: "duplicate"`.

**400 — validation_error**: body que no es JSON válido, payload
inválido/incompleto, id de Odoo referenciado inexistente, adjunto inválido, o
montos fuera de tolerancia con `action_if_exceeded: "reject"`. Cada mensaje
en `details` incluye el path JSON del campo (ej. `"lines[0].unit_price"`).
Genera log.

**401**: falta el header `Authorization`, no es `Basic`, o usuario/contraseña
inválidos. **No** genera log y tiene una forma reducida (sin `success` ni
listas):
```json
{"status": "validation_error", "message": "Usuario o contraseña inválidos"}
```

**404**: no lo devuelve el módulo; es Odoo indicando que el path no existe
(ver sección Endpoint).

**405**: método distinto de `POST`.

**422 — pending_review**: proveedor no resuelto y `policy_if_missing`
distinto de `"create"`. No crea la factura.

**500 — processing_error**: excepción inesperada; nunca incluye traceback
(queda en el log del servidor y el registro de log pasa a
`processing_error`).

## Log de importación

Cada request autenticado crea un registro `purchase.invoice.import.log`,
visible en **Contabilidad → Proveedores → Importación Facturas de Compra
(API)**. Estados: `received`, `created`, `duplicate`, `validation_error`,
`pending_review`, `processing_error`. Guarda el payload crudo (con el PDF
redactado), los checks propios y los del proveedor (solo informativos), los
warnings, el contacto resuelto/creado, la factura creada o duplicada y el
adjunto.

Permisos: lectura para *Facturación* (`account.group_account_invoice`),
lectura/escritura/creación/borrado para *Administrador de contabilidad*
(`account.group_account_manager`).

## Configuración (`ir.config_parameter`)

Editable desde Ajustes → bloque "Importación de Facturas de Compra (API)"
(campo "Tolerancia de totales"), o directamente:

| Clave | Obligatoria | Descripción |
|---|---|---|
| `gc_odoo_purchase_invoice_import_api.total_tolerance` | No (default `1.0`) | Tolerancia de diferencia de montos, en la moneda del comprobante, usada solo si `validation.tolerance` no viene en el payload. |

Nota operativa: `ir.config_parameter` cachea sus valores en memoria; un
cambio hecho por SQL directo (fuera del ORM) no se refleja hasta que se
invalide el caché o se reinicie el proceso.

## Cómo correr los tests

Entorno real (`docker-compose.yml`/`entrypoint.sh` en la raíz del proyecto):
contenedor Odoo `gauchocode/docker-odoo:16.0`, Postgres accesible como host
`postgres` (usuario/clave `odoo`/`odoo` en este entorno de desarrollo), config
en `/var/lib/odoo/odoo.conf` (con `db_host=localhost`, por lo que hay que
sobrescribirlo con `--db_host=postgres` al ejecutar `odoo` a mano, ya que el
`entrypoint.sh` lo hace automáticamente al arrancar el contenedor).

Instancias donde está instalado (verificado): contenedor
`potenciar_dev-odoo-1` / base `potenciar_dev`, y contenedor
`potenciar_qwerty_dev-odoo-1` / base `qwerty_dev`.

```bash
docker exec <contenedor_odoo> odoo \
  -c /var/lib/odoo/odoo.conf \
  --db_host=postgres --db_port=5432 --db_user=odoo --db_password=odoo \
  -d <nombre_base> \
  -u gc_odoo_purchase_invoice_import_api \
  --test-enable \
  --test-tags /gc_odoo_purchase_invoice_import_api \
  --stop-after-init \
  --no-http --workers=0 \
  --log-level=test
```

Usar `-i` en vez de `-u` la primera vez (módulo no instalado todavía).
`--no-http --workers=0` evita el conflicto de puerto con el proceso Odoo que
ya está corriendo en el contenedor.

`test_payload_validator.py` corre como `unittest.TestCase` puro (sin acceso a
Odoo, usa ids ficticios de `tests/fixtures/valid_v01_single_line.json` tal
cual) y `test_invoice_importer.py` como `TransactionCase` (crea sus propios
records en `setUpClass` e inyecta esos ids reales en una copia del fixture);
ambos se descubren y ejecutan con el mismo comando de arriba.

## Ejemplo `curl`

```bash
curl -X POST https://dev.potenciar.lograerp.com/api/v1/purchase-invoices \
  -u "servicio_proveedor:<contraseña>" \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/valid_v01_single_line.json
```

(Ajustar los ids bajo `odoo.*` a records reales de la base destino antes de
probar contra un servidor real.)

### Postman

- Método: `POST`.
- URL: `https://dev.potenciar.lograerp.com/api/v1/purchase-invoices` (sin
  `/import` ni otro sufijo).
- Authorization: tipo *Basic Auth* con usuario y contraseña de Odoo.
- Body: *raw* → *JSON*, con el payload v0.1.

Para diagnosticar qué path llegó realmente al servidor:

```bash
docker logs potenciar_dev-odoo-1 2>&1 | rg -a "api/v1/purchase-invoices"
```

Ver `DECISIONES.md` para el detalle de decisiones técnicas, limitaciones y
puntos pendientes de confirmación con el cliente.
