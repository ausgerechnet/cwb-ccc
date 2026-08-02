source("ccc-utils.R")

d <- read_tsv("~/Downloads/sascha/diachRo-input-cooc-contrat-2y-xtab.tsv") |>
  mutate(across(where(is.numeric), ~ na_if(.x, 0)))

ccc_pairwise_overlap_col(d, "T1984", "T1986", method = "kappa")
ccc_pairwise_overlap_col(d, "T1984", "T1986", method = "rbo")

source("~/Downloads/sascha/ufa.inc.R")


ccc.pairwise.overlap.cols(d, "T1984", "T1986", method = "kappa")
# diese Funktion interpretiert AM = 0 in Deiner Tabelle nicht als Cut-Off und ordnet Items relativ arbiträr an, vergibt also unterschiedliche Ranks für Items mit AM = 0
