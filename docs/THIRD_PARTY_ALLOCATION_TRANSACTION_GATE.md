# Third-party Vocabulary Allocation Transaction Gate

## Status

actual third-party Stable Vocabulary allocation 已完成，并通过 transaction gate。

```text
execution run          = 34608158097 / PASS
allocation commit      = fe0d1f04c2eae1cf5d492673dd79aef302691d39
committed-state check  = 34608453454 / PASS
```

当前不再处于 `authorized-pending-apply`；allocation authorization 已消费并关闭。Standing directive 仍然有效，用于后续 Learner / Review / Release pipeline step。

---

## 1. Executed transaction scope

allocation commit 精确只改变：

```text
anki/klose/master/note_registry_extensions.csv
anki/klose/third_party_vocabulary/provenance/stable_evidence_bindings.csv
```

没有改变：

```text
anki/klose/master/source_identity_extensions.csv
anki/klose/learner/
anki/klose/publish/
anki/klose/anki/
anki/klose/expressions/
release registry / FSRS / Review History / Due / Card State
```

GitHub commit API 已再次确认 allocation commit 只有上述两个 path。

---

## 2. Executed validation sequence

实际执行顺序：

```text
execution request from current user “继续处理”
→ closed-state provenance / plan / dry-run preflight
→ runner-local authorization transition
→ authorized control-plane revalidation
→ actual allocator
→ persistent-state checker
→ independent post-mutation Completion Recheck
→ stage exactly two files
→ local allocation commit
→ persistent-state recheck
→ post-commit Completion Recheck
→ squash tested data onto immutable remote base
→ compare-and-swap remote-main check
→ push exact two-path commit
→ durable committed-state validator
```

任何 preflight / recheck / CAS 失败都会阻止 remote persistence。

---

## 3. Result

```text
historical extension rows unchanged = 392
new Stable rows exact               = 1821
new range                           = KV001195..KV003015
persistent Stable rows              = 3015
active Stable NoteIDs               = 3010
external evidence bindings          = 15791
held identities allocated/bound     = no
```

Committed-state validator：

```text
tools/validate_third_party_allocation_committed_state.py
```

Execution receipt：

```text
anki/klose/third_party_vocabulary/allocation/execution_receipt.json
```

---

## 4. Historical failed attempt

run `34608014656`：

```text
actual apply                         = PASS
persistent-state                     = PASS
post-mutation Completion Recheck     = PASS
remote push                          = no
```

失败原因是 transaction shell 使用 `git diff --name-only` 做 scope check，而新建的 `stable_evidence_bindings.csv` 当时是 untracked，不会出现在该命令结果里，因此集合比较误报失败。

修复为基于 `git status --short` 同时统计 tracked + untracked 后，retry `34608158097` 完整通过。该失败没有留下部分 remote mutation。

---

## 5. Standing directive after allocation

项目目标仍是：

```text
处理第三方 Vocabulary 到只剩最终合入 Klose 当前 Anki
```

在此之前：

```text
用户说“继续” / “继续处理”
→ 授权执行当前下一 pipeline step
```

allocation step 已消费；不得重复 allocation。下一 pipeline step 读取根目录 `NEXT.md`，当前为 Learner Presentation + Learning Admission preparation。
