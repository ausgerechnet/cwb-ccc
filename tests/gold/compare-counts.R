library(data.table)

ccc <- fread("ccc-germaparl1114-atomkraft.tsv.gz")[,c("V1", "O11")]
names(ccc) <- c("lemma", "ccc")
ucs <- fread("ucs-germaparl1114-atomkraft.ds.gz", quote="")[, c("l2", "f")]
names(ucs) <- c("lemma", "ucs")

df <- merge(ccc, ucs)
sum(df$ccc != df$ucs)
