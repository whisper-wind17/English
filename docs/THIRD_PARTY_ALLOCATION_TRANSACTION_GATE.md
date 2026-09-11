# Third-party Vocabulary Allocation Transaction Gate

## Purpose

本 gate 解决 future **actual third-party Stable Vocabulary allocation** 的事务安全，并定义当前用户授权语义。

当前状态：

```text
Authorized                        = false
ActualMutationAuthorized          = false
StableNoteIDAllocationAuthorized  = false
actual third-party Stable rows    = 0
actual evidence bindings          = 0
current max NoteID                = KV001194
```

项目目标是把第三方 Vocabulary 全部处理到 **只剩最终合入 Klose 当前 Anki** 的状态。在达到该目标之前，用户已给出 standing directive：

```text
用户说“继续”
→ 授权执行当前流水线的下一步动作
→ 每次只推进一个受 gate 保护的 pipeline step
```

因此，在该目标未完成前，`继续` 可以触发下一个必要 mutation step，包括 Stable NoteID allocation；不再要求额外重复“授权执行……”措辞。所有机器 gate、truth-boundary、Completion Recheck 仍必须照常通过。

---

## 1. Authorized transaction scope

allocation transaction 只允许改变：

```text
anki/klose/master/note_registry_extensions.csv
anki/klose/third_party_vocabulary/provenance/stable_evidence_bindings.csv
```

禁止同事务改变：

```text
anki/klose/master/source_identity_extensions.csv
anki/klose/learner/
anki/klose/publish/
anki/klose/anki/
anki/klose/expressions/
release registry / FSRS / Review History / Due / Card State
```

---

## 2. Pre-apply gate

执行 actual apply 前必须重新验证：

```text
Stage-B decisions               = 2820 / 2820
review queue / selected         = 0 / 0
reuse / new / held              = 903 / 1821 / 96
Stable baseline                 = 1194 persistent / 1189 active
current max NoteID              = KV001194
truth-boundary blobs            = exact current committed blobs
provenance contract             = current
allocation authorization        = standing directive + current “继续” evidence, or equivalent explicit authorization
authorized gates                = Actual + StableNoteID only
Master/Learner/Release/Publish/Anki gates = false
```

然后重新生成并独立验证 mutation-disabled dry run。

---

## 3. Post-mutation Completion Recheck

独立 checker：

```text
tools/validate_third_party_allocation_post_mutation.py
```

它不复用 mutator 内部状态，而是从 committed baseline、validated dry-run 和当前工作树重新核对：

```text
historical extension rows unchanged
new Stable rows exact                  = 1821
post-allocation full Stable rows       = 3015
external evidence bindings exact       = 15791
held identities allocated              = no
allowed Git diff scope                 = exactly two authorized paths
Master/Learner/Release/Publish/Anki    = unchanged
```

同时继续运行：

```text
KLOSE_BASE_COMMIT=<authorization-base> python tools/check_klose_persistent_state.py
```

确保历史 NoteID / PrimaryOriginKey / identity-defining fields 不漂移。

---

## 4. Commit transaction gate

验证顺序固定：

```text
standing-directive/current-step authorization transition
→ provenance / plan validation
→ dry-run build + independent validation
→ actual allocator writes working tree
→ persistent-state checker
→ independent post-mutation Completion Recheck
→ git diff --check
→ stage exactly two authorized files
→ commit
→ persistent-state checker again against authorization baseline
→ post-mutation Completion Recheck again against authorization baseline
→ verify allocation commit contains exactly two paths
→ only then may remote persistence be considered
```

任何一步失败，transaction 不得继续提交/推送。

并发 main 变化必须导致旧 truth boundary 失效并重新 preflight，不能 rebase 后静默沿用旧 allocation plan。

---

## 5. Isolated transaction validation

`Third-party Allocation Plan Validation` workflow 在 repo 外 isolated local clone 中完整演练真实 transaction：

```text
local authorization transition
→ authorized-pending-apply validation
→ actual --apply in isolated clone
→ 1821 exact Stable appends
→ 15791 exact evidence bindings
→ persistent-state PASS
→ post-mutation Completion Recheck PASS
→ stage exactly two files
→ local allocation commit
→ post-commit persistent-state PASS
→ post-commit Completion Recheck PASS
→ remote push = no
```

Validation run：

```text
34596833236 / PASS
```

关键结果：

```text
historical extension rows unchanged = 392
new Stable rows exact               = 1821
full Stable NoteIDs                 = 3015
external evidence bindings exact    = 15791
held identities allocated           = no
Master/Learner/Release/Publish/Anki = unchanged
remote push                         = no
```

这证明 transaction mechanism 已可验证；当前 repo truth 仍未执行 actual allocation。

---

## 6. Current next-step semantics

当前仍保持：

```text
Authorized                       = false
actual allocation                = NOT AUTHORIZED / NOT STARTED
note_registry_extensions max     = KV001194
stable_evidence_bindings.csv     = absent
```

但不再设置人工 HOLD POINT。只要项目尚未达到“只剩最终 Anki 合入”的状态，用户下一次说：

```text
继续
```

就应把它作为当前下一 pipeline step 的授权证据，执行 preflight → authorization transition → 当前下一步动作，并在该步骤完成后再次 CHECKPOINT。
