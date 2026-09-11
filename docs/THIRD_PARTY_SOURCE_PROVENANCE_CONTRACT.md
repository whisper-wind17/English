# Third-party Vocabulary Source Provenance Contract

## Purpose

第三方教材整理数据需要保留 provenance，但它与 **Klose 已核实的教材 Source Fact** 不是同一层事实。

当前 20 个 third-party adapters 来自第三方整理 XLSX。它们可以作为 Vocabulary Identity 的外部证据，但当前 occurrence schema 没有 `SourceEdition / Revision`，因此不能因为一个词被纳入 Stable Vocabulary，就反向宣称它属于某个已核实教材版本。

本契约将两种 provenance 明确分离：

```text
External Evidence Provenance
    = 第三方整理数据实际提供了什么

Verified Textbook Source Fact
    = 经实际教材/同 edition 官方证据核实后，教材在哪个版本、书册、位置出现
```

机器契约：

```text
anki/klose/third_party_vocabulary/provenance/contract.json
```

验证入口：

```text
tools/validate_third_party_source_provenance.py
```

---

## 1. Current external-evidence boundary

第三方 SOURCE FREEZE 当前固定：

```text
enabled adapters             = 20
source occurrences           = 18887
source adapters fingerprint  = fdf79e5f48ed77d543dc05f3d347c3ce03d406e4884c89a426fdac8fa20e8272
unified occurrences fingerprint = b025cb4f69b030da3664ab9b1bdd8500cb0166b122392b282a4293567702a7d4
```

每条 external evidence 的稳定主键是：

```text
SourceOccurrenceKey
```

整个 evidence set 还必须绑定 `UnifiedOccurrencesFingerprint`。只保留 occurrence key 而不绑定 snapshot 不够，因为未来 source adapter 可能重新解析或 source corpus 可能变化。

当前 occurrence schema：

```text
SourceOccurrenceKey
SourceID
SourceBook
Grade
Semester
SourceRow
Word
MatchKey
British
American
Definition
SourceFile
```

当前明确事实：

```text
SourceEdition fact present = false
EditionStatus              = unverified
```

`unverified` 是证据状态，不是一个教材版本名称。

---

## 2. SourceEdition policy

禁止以下做法：

```text
SourceEdition = unknown
SourceEdition = unverified
SourceEdition = third-party
SourceEdition = klose-current
```

如果这些值被直接写进 Master `SourceEdition` 字段，会把“我们不知道版本”伪装成“这是一个版本标识”。因此当前 Master Source Identity Map **不接受 unknown sentinel**。

同样禁止从以下信息推断 edition：

- 文件名；
- Grade / Semester；
- 第三方目录或整理标签；
- `SourceID` 中的 start1/start3；
- 与另一份教材数据表面相似。

只有真实 source evidence 可以建立 Verified Textbook Source Fact，例如：

```text
Klose 实际教材照片/扫描件
> 可确认同 Edition 的官方材料
> 第三方整理 XLSX
```

这与 `docs/SOURCE_RECONCILIATION.md` 一致。

---

## 3. Stable Identity can use external evidence

Vocabulary Identity 回答“这个 learning unit 是否应该长期存在”，Textbook Source Fact 回答“教材哪个版本在哪里出现”。二者不需要绑定为同一个事务。

因此：

```text
External Evidence may support Stable Identity Allocation = yes
Stable Identity Allocation implies verified textbook provenance = no
```

未来若用户显式授权 1821 个 reviewed `new-stable-identity` proposal 的 allocation，Stable Registry origin 使用第三方 identity boundary，而不是伪造教材 occurrence：

```text
PrimaryOriginKey  = third-party-vocabulary|<ProvisionalIdentityKey>
CreatedSource     = third-party-vocabulary
CreatedSourceBook = external-evidence-corpus
```

这里 `CreatedSourceBook=external-evidence-corpus` 明确表示创建来源类别，不是教材版本。

903 个 `reuse-existing` 不改变现有 Stable Registry identity；它们只建立 external evidence 对现有 NoteID 的证据关系。

96 个 `held` 仍不建立 NoteID 关系。

---

## 4. Future stable evidence binding

实际 allocation 被授权并完成后，第三方 evidence 与 Stable NoteID 的关系进入独立表，而不是直接写入 Master textbook source map：

```text
anki/klose/third_party_vocabulary/provenance/stable_evidence_bindings.csv
```

计划 schema：

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

当前 external evidence 状态固定为：

```text
EvidenceStatus = external-unverified-edition
```

该表只在 future authorized allocation 后生成。目前文件必须不存在，避免 plan 阶段提前制造 NoteID binding。

External evidence binding 的职责是回答：

> 为什么这个 Stable Identity 当时被认为值得建立或与现有 identity 等价？

它不回答：

> Klose 的某一本真实教材在什么 edition 出现了这个词？

---

## 5. Promotion to Master Source Fact

只有某条 occurrence 后续拿到可验证的 SourceEdition / Revision 证据，才能建立：

```text
anki/klose/master/source_identity_extensions.csv
```

所需事实至少包括：

```text
SourceID
verified SourceEdition / Revision
SourceItemKey
NoteID
Decision
Status
```

Promotion 是 **增加 Verified Textbook Source Fact**，不是删除原来的 external evidence。两者应同时保留，以维持审计链：

```text
third-party external evidence
→ later verified textbook evidence
→ Master Source Identity Map row
```

同一个 `SourceID` 可以同时存在已核实 Master mappings 和未核实 third-party occurrences；关键在于不能把未核实的 `SourceOccurrenceKey` 偷渡进 Master mapping。

---

## 6. Effect on allocation gate

此 contract 解决了此前的 SourceEdition 架构 blocker：**Stable Identity allocation 本身不需要伪造 SourceEdition**。

因此 provenance contract 完成后，missing SourceEdition 不再是 identity allocation 的硬 blocker；它继续阻止的是：

```text
unverified third-party occurrence
→ Master textbook source mapping
```

当前仍然保持：

```text
MasterSourceMappingMutationAuthorized = false
StableNoteIDAllocationAuthorized      = false
AnkiMutationAuthorized                = false
```

StableNoteID allocation 之所以仍为 false，是因为：

1. 用户尚未显式授权 actual allocation / merge；
2. append-only allocator 与 future evidence-binding implementation 尚未完成其独立 Validation Gate。

这两个 blocker 与 SourceEdition 已经解耦。

---

## 7. Invalidation

以下任一变化要求 provenance contract recheck：

- `source_freeze.json` 变化；
- enabled adapter set 变化；
- adapter occurrence schema 变化；
- unified occurrence fingerprint 变化；
- Master Source Identity Map schema 变化；
- future evidence binding schema 变化。

如果未来 adapter 正式补入真实 `SourceEdition` 字段，本 v1 contract 应主动失败，要求重新设计，而不能静默继续把这些数据当作 unverified evidence。

---

## 8. Validation checkpoint

本契约已经完成机器验证：

```text
validation workflow run = 34585155788 / PASS
validation job          = 103217537427 / PASS
```

验证确认：

```text
external-evidence adapters               = 20
external-evidence occurrences            = 18887
source-freeze fingerprints               = current
SourceEdition fact in adapters           = no
synthetic/unknown SourceEdition in Master = forbidden
external evidence may support Stable identity = yes
Stable identity implies textbook provenance   = no
unverified occurrence promoted to Master map  = no
Master source mapping mutation authorized     = no
Stable NoteID allocation authorized           = no
Anki mutation authorized                      = no
validation workspace mutation                 = no
```

因此 provenance contract 当前状态为：

```text
IMPLEMENTED / VALIDATED / CHECKPOINTED
```
