# Вариант 16 — команды для защиты этапов 4 и 5

## Команды для защиты: этапы 4 и 5

Код этапов 1–3 не изменялся. Команды вводятся в Terminal из корневой папки проекта `second_16`.
Для демонстрации обоих этапов удобнее оставаться на ветке `5`:
она содержит реализацию этапа 4 и этапа 5.

Перейти на итоговую ветку:

```bash
git switch 5
```

### Этап 4. Порядок загрузки зависимостей

**1. Показать правильный порядок установки пакетов** на тестовом репозитории:

```bash
./run_stage4.sh --package A --repository tests/diamond-repository.txt --test-mode --max-depth 10 --install-order
```

Ожидаемый порядок: `D`, затем `B` и `C`, затем `A`.
Пакет `D` устанавливается первым, потому что от него зависят `B` и `C`.

**2. Показать обработку циклических зависимостей:**

```bash
./run_stage4.sh --package A --repository tests/cycle-repository.txt --test-mode --max-depth 10 --install-order
```

Ожидается сообщение об ошибке `Dependency cycle blocks installation order`.
При цикле корректный порядок установки построить нельзя.

**3. Сравнить результат с настоящим Alpine APK:**

```bash
./run_stage4.sh --package curl --repository https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64/ --max-depth 100 --install-order --compare-apk
```

Для сравнения нужен установленный `apk` или запущенный Docker.
Используется режим `apk add --simulate`: пакеты не устанавливаются.

### Этап 5. Визуализация графа в D2

**1. Установить D2 (один раз):**

```bash
curl -fsSL https://d2lang.com/install.sh | sh -s --
```

Проверить установку:

```bash
d2 version
```

**2. Построить граф для пакета A:**

```bash
./run_stage5.sh --package A --repository tests/test-repository.txt --test-mode --max-depth 10
```

**3. Построить граф для пакета B:**

```bash
./run_stage5.sh --package B --repository tests/test-repository.txt --test-mode --max-depth 10
```

**4. Построить граф для пакета C:**

```bash
./run_stage5.sh --package C --repository tests/test-repository.txt --test-mode --max-depth 10
```

Каждая команда выводит описание графа D2, создаёт SVG-изображение
и открывает его. Файл по умолчанию сохраняется во временную папку.

**Вместо трёх отдельных команд можно запустить общую демонстрацию:**

```bash
./scripts/demo_stage5.sh
```

Скрипт последовательно строит графы для `A`, `B` и `C`.

### Общая проверка проекта

Запустить все автоматические тесты:

```bash
python3 -m unittest discover -s tests -v
```

Ожидаемый результат: `Ran 34 tests` и `OK`.

Показать ветки и историю коммитов:

```bash
git branch -v
git log --oneline --decorate --all -10
```

Отправить ветки 4 и 5 на GitHub:

```bash
git push -u origin 4
git push -u origin 5
```

---

## Overview

A command-line Alpine Linux (`apk`) dependency analyzer implemented with
Python's standard library. It downloads package records directly from an
Alpine `APKINDEX.tar.gz` or loads a local text test repository.

Stage 2 retrieved direct dependencies; **stage 3** traverses transitive
dependencies with **recursive BFS**. Each recursive call processes the next
breadth-first layer. A visited set handles cycles, and `--max-depth` limits
how many edges are explored. Cyclic edges remain in the reported graph.

## CLI parameters

| Option | Description |
|---|---|
| `--package NAME` | Package to analyze, required |
| `--repository PATH_OR_URL` | Remote Alpine repository directory or local graph file |
| `--test-mode` | Interpret repository as a local graph file |
| `--max-depth N` | BFS limit in edges, integer 0–100; default 3 |

The remote URL must point to a specific repository, e.g. a `main/x86_64/`
folder containing `APKINDEX.tar.gz`, not simply the Alpine website root.
Special virtual dependencies (`so:`, `cmd:`, `pc:`) are not resolved. Named
package constraints are normalized to names for this graph demonstration.

## Run (macOS / Linux)

```bash
./run.sh --package A --repository tests/test-repository.txt --test-mode
./run.sh --package A --repository tests/cycle-repository.txt --test-mode
./run.sh --package A --repository tests/diamond-repository.txt \
  --test-mode --max-depth 1
./run.sh --package busybox --repository \
  https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64/ \
  --max-depth 2
```

For Windows, use `run.bat` instead of `./run.sh`.

## Test repository format

Packages use **uppercase Latin letters**. Each line is `NAME: DEP1, DEP2`;
blank dependency lists are permitted. Blank lines and `#` comments are
ignored. Examples are in `tests/`.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Limitations and errors

Invalid options, missing files or packages, malformed graph files,
unavailable repositories and damaged archive data produce error messages.
This educational tool does not implement Alpine virtual package providers,
architecture selection, pinning or cross-repository version resolution.
The output is a sorted adjacency list, not an image (visualization is stage 5).

## Stage 4 — installation order

Stage 4 calculates a safe installation order from the dependency graph.
Dependencies are listed before the package that requires them. The order is
calculated deterministically; a cycle is reported because it prevents a valid
topological installation order. If `--max-depth` cuts off the graph, the
program warns which packages were not fully explored.

Run with a local test repository:

```bash
./run_stage4.sh --package A \
  --repository tests/diamond-repository.txt \
  --test-mode --max-depth 10 --install-order
```

Check cycle handling:

```bash
./run_stage4.sh --package A \
  --repository tests/cycle-repository.txt \
  --test-mode --max-depth 10 --install-order
```

Compare with the real Alpine package manager using an Alpine repository:

```bash
./run_stage4.sh --package curl \
  --repository https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64/ \
  --max-depth 100 --install-order --compare-apk
```

The comparison uses `apk add --simulate`, so it does not install packages.
It uses the local `apk` command when available or a disposable Docker Alpine
container otherwise. Differences can occur because APK resolves package
versions, virtual dependencies, architecture and already installed packages;
the analyzer builds a name-based graph from one repository index.

## Stage 5 — D2 visualization

Stage 5 converts the graph into the D2 diagram language, prints the D2 source,
renders an SVG image and opens it in the default image viewer. By default the
SVG is written to a temporary file outside the repository. Use `--output` to
save it to a chosen path, or `--no-open` to skip opening the image.

Install the D2 command-line tool using the
[official installation instructions](https://d2lang.com/tour/install/):

```bash
curl -fsSL https://d2lang.com/install.sh | sh -s --
d2 version
```

Visualize one package:

```bash
./run_stage5.sh --package A \
  --repository tests/test-repository.txt \
  --test-mode --max-depth 10
```

The three-package demonstration uses packages `A`, `B` and `C` from the test
repository and opens each generated diagram:

```bash
./scripts/demo_stage5.sh
```

To save an image instead of using a temporary file:

```bash
./run_stage5.sh --package A \
  --repository tests/test-repository.txt \
  --test-mode --output graph-A.svg
```
