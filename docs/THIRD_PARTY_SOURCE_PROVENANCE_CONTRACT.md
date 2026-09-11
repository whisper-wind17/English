# Third-party Vocabulary Source Provenance Contract

## Current status

第三方 Vocabulary Stable allocation 已完成，但 provenance boundary **没有改变语义**：

```text
External Evidence Provenance
!=
Verified Textbook Source Fact
```

Current execution truth：

```text
allocation commit          = fe0d1f04c2eae1cf5d492673dd79aef302691d39
new Stable rows            = 1821
external evidence bindings = 15791
max NoteID                 = KV003015
```

actual allocation 后已经存在：

```text
anki/klose/third_party_vocabulary/provenance/stable_evidence_bindings.csv
```

它记录 third-party evidence → Stable NoteID 的审计关系，不代表任何教材 Edition / Revision 已核实。

---

## 1. External-evidence boundary

SOURCE FREEZE：

```text
enabled adapters                 = 20
source occurrences               = 18887
source adapters fingerprint      = fdf79e5f48ed77d543dc05f3d347c3ce03d406e4884c89a426fdac8fa20e8272
unified occurrences fingerprint = b025cb4f69b030da3664ab9b1bdd8500cb0166b122392b282a4293567702a7d4
```

稳定 evidence key：

```text
SourceOccurrenceKey
+ UnifiedOccurrencesFingerprint
```

当前 occurrence schema 仍没有真实：

```text
SourceEdition / Revision
```

因此：

```text
SourceEdition fact present = false
EditionStatus              = unverified
```

`unverified` 是 evidence status，不是 Edition 名称。

---

## 2. SourceEdition policy

禁止把以下值写成 Master SourceEdition：

```text
unknown
unverified
third-party
klose-current
```

也禁止从以下信息猜 Edition：

- 文件名；
- Grade / Semester；
- 第三方目录标签；
- `SourceID` 的 start1/start3；
- 与其他教材的表面相似。

Verified Textbook Source Fact 只能来自真实 source evidence，例如：

```text
Klose 实际教材照片 / 扫描件
> 可确认同 Edition 的官方材料
> 第三方整理数据
```

---

## 3. Stable identity allocation and provenance

规则：

```text
External Evidence may support Stable Identity Allocation = yes
Stable Identity Allocation implies verified textbook provenance = no
```

本次 allocation 新 identity origin：

```text
PrimaryOriginKey  = third-party-vocabulary|<ProvisionalIdentityKey>
CreatedSource     = third-party-vocabulary
CreatedSourceBook = external-evidence-corpus
```

其中 `external-evidence-corpus` 是创建 evidence 类别，不是教材版本。

Stage-B 执行结果：

```text
reuse-existing       = 903
new-stable-identity  = 1821
held                 = 96
```

903 reuse 不改原 Stable identity；1821 new 追加 Stable identity；96 held 不建立 NoteID binding。

---

## 4. Stable evidence binding — now materialized

文件：

```text
anki/klose/third_party_vocabulary/provenance/stable_evidence_bindings.csv
```

schema：

```text
NoteID
ProvisionalIdentityKey
SourceOccurrenceKey
SourceID
SourceBook
Grade
Semester
SourceRow
SourceSnapshotFingerprint
EvidenceStatus
```

Current truth：

```text
rows           = 15791
EvidenceStatus = external-unverified-edition
```

15791 rows 只覆盖 Stage-B：

```text
reuse-existing + new-stable-identity
```

96 held 对应 evidence 不绑定 Stable NoteID。

该表回答：

> 哪些冻结的 third-party evidence 支撑了当时的 Stable identity 判断？

它不回答：

> Klose 某一本真实教材的哪个 Edition 在哪里出现这个词？

---

## 5. Promotion to Master Source Fact

只有未来获得独立可验证的 SourceEdition / Revision evidence，才允许写：

```text
anki/klose/master/source_identity_extensions.csv
```

Promotion 是增加 Verified Textbook Source Fact，不删除 external evidence binding。

审计链应保持：

```text
third-party external evidence
→ Stable identity/evidence binding
→ later verified textbook evidence
→ Master Source Identity mapping
```

当前：

```text
MasterSourceMappingPromotionAuthorized = false
```

---

## 6. Allocation validation

Execution receipt：

```text
anki/klose/third_party_vocabulary/allocation/execution_receipt.json
```

Committed-state checker：

```text
tools/validate_third_party_allocation_committed_state.py
```

实际验证：

```text
execution run              = 34608158097 / PASS
allocation commit          = fe0d1f04c2eae1cf5d492673dd79aef302691d39
committed-state validation = 34608453454 / PASS
```

确认：

```text
unverified occurrence promoted to Master map = no
Master source mapping mutation                = no
Learner / Release / Publish / Anki mutation   = no
```

---

## 7. Invalidation

以下变化要求 provenance recheck：

- `source_freeze.json` 变化；
- enabled adapter set 变化；
- occurrence schema 变化；
- unified occurrence fingerprint 变化；
- `stable_evidence_bindings.csv` schema / key semantics 变化；
- Master Source Identity Map schema 变化；
- adapter 新增真实 `SourceEdition` 字段。

如果未来 adapter 正式携带真实 Edition，本 v1 external-unverified contract 必须重新设计，不能静默继续沿用。
