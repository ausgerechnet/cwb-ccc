library(tidyverse)

path.in <- 
dir.out <- 

# function for the automatic extraction of good collocation candidates
# (ensemble model using the following AMs)

.ams.default <- c(
  "conservative_log_ratio",
  "log_ratio",
  "mutual_information",
  "dice",
  "liddell",
  "local_mutual_information",
  "min_sensitivity",
  "simple_ll",
  "log_likelihood",
  "t_score",
  "z_score"
)

retrieve.good.collocates <- function(df, n_word, n_pos, ratio = .5, ams = .ams.default){
  size <- df |> filter(node_word == n_word, node_pos == n_pos) |> nrow()
  n <- floor(size * ratio)
  if (n == 0){
    return(tibble())
  }
  ranks <- tibble()
  for (am in ams){
    items.am <- df |> 
      filter(node_word == n_word) |> 
      arrange_at(am, desc) |>
      head(n) |> 
      pull(candidate_word)
    ranks.am <- tibble(measure = am, item = items.am, rank = 1:length(items.am))
    ranks <- rbind(ranks, ranks.am)
  }
  a <- ranks |> pivot_wider(names_from = measure, values_from = rank)
  a <- a[complete.cases(a),]
  a <- a |> mutate(avg_rank = rowMeans(a |> select(- item))) |> 
    arrange(avg_rank)
  return(a)
}

tab <- read_tsv(path.in)

selection.pos <- tab |> select(node_word, node_pos) |> distinct()

for (i in 1:nrow(selection.pos)){
  row <- selection.pos[i,]
  print(str_c(row$node_word, " (", row$node_pos, ")"))
  d <- retrieve.good.collocates(tab, row$node_word, row$node_pos)
  d |> write_tsv(str_c(dir.out, row$node_word, "-", row$node_pos, ".tsv"))
}
