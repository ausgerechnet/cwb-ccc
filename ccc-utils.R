library(tidyverse)
library(lubridate)
library(kableExtra)
library(DT)
library(colorspace)
library(matrixStats)
library(anomalize)
library(gespeR)
library(irr)
library(gridExtra)

# function for formatting concordance lines
concordance.format <- function(conc, n = 10){
  conc %>%
    head(n) %>%
    select(c("left_word", "node_word", "right_word")) %>%
    kbl(booktabs = T, align = c("rcl"), longtable = T,
        col.names = c("left context", "node", "right context"),
        table.attr = "style = \"color: white; background-color: black;\"") %>%
    row_spec(0, bold = T) %>%
    column_spec(c(1, 3), width = "6cm") %>%
    column_spec(2, bold = T, width = "3cm") %>%
    kable_styling(latex_options = "striped")
}

# function for plotting collocates
collocates.plot <- function(df.plot,
                            am = 'conservative_log_ratio',    # x-axis
                            significance = 'log_likelihood',  # shade
                            size = 'marginal',
                            max_item_length = 30){
  
  # deal with row names if necessary
  if(! 'item' %in% names(df.plot)){
    df.plot$item <- row.names(df.plot)
  }

  # cut items that are too long
  df.plot$item <- str_sub(df.plot$item, 1, max_item_length)
  
  # encode significance thresholds
  df.plot$significance <- cut(df.plot[, significance],
                              breaks = c(0, qchisq(.95, 1), qchisq(.99, 1), qchisq(.999, 1), Inf),
                              labels = c("", "*", "**", "***"),
                              ordered_result = T)
  
  # plot
  df.plot %>% 
    ggplot(aes_string(x = nrow(df.plot):1,
                      y = am,
                      colour = "significance",
                      size = size)) +
    geom_point() +
    scale_color_manual(values = sequential_hcl(5, palette = "Grays")[4:1], drop = FALSE) +
    scale_x_continuous(breaks = nrow(df.plot):1, labels = df.plot$item) +
    labs(x = NULL, y = am) +
    coord_flip()

}

# function for translating UFA collocates into data frame
ufa.table <- function(tables, am = 'log_likelihood'){
  
  # get tables
  df <- data.frame(item = character())
  for (i in 1:length(tables)){
    new.table <- tables[[names(tables)[i]]] %>% 
      py_to_r %>%
      # filter(log_likelihood > qchisq(.999, 1)) %>%
      arrange(desc(!!sym(am)))
    new.items <- row.names(new.table)
    new.df <- data.frame(item = new.items, rank = 1:length(new.items))
    names(new.df)[2] <- names(tables)[i]
    df <- merge(df, new.df, all = TRUE, by = "item")
  }
  
  # add average rank (unobserved = Inf)
  row.names(df) <- df$item
  df <- df[, 2:ncol(df)] %>%
    replace(is.na(.), Inf) %>%
    mutate(average_rank = rowMedians(as.matrix(.))) %>%
    arrange(average_rank)
  
  return(df)
}

# function for calculating average overlap between two data frames stored in list of tables arranged by given am
pairwise.overlap <- function(tables, name1, name2, am = "log_likelihood", cut_off = 100, p = .95){
  
  # create top-cut_off-list according to column1
  left <- tables[[name1]] %>%
    py_to_r() %>%
    arrange(desc(!!sym(am))) %>%
    head(cut_off)
  left.list <- left[, am]
  names(left.list) <- row.names(left)

  right <- tables[[name2]] %>%
    py_to_r() %>%
    arrange(desc(!!sym(am))) %>%
    head(cut_off)
  right.list <- right[, am]
  names(right.list) <- row.names(right)

  # calculate rbo
  value = rbo(left.list, right.list, p)
  
  return(value)
}

# function for calculating average overlap between two columns
pairwise.overlap.2 <- function(df, column1, column2, cut_off = 100, p = .95, method = "rbo"){
  
  if (method == "rbo"){

    # create top-cut_off-list according to column1
    left <- df %>% 
      arrange(desc(!!sym(column1))) %>%
      head(cut_off)
    left.list <- left[, column1]
    names(left.list) <- row.names(left)
    
    # create top-cut_off-list according to column2
    right <- df %>%
      arrange(desc(!!sym(column2))) %>%
      head(cut_off)
    right.list <- right[, column2]
    names(right.list) <- row.names(right)

    # calculate rbo
    value = rbo(left.list, right.list, p)
  }

  else if (method == "kappa"){
    
    # create input data frame
    df.input <- df %>%
      arrange(desc(!!sym(column1))) %>%
      mutate(rank.left = 1:n()) %>%
      arrange(desc(!!sym(column2))) %>%
      mutate(rank.right = 1:n()) %>%
      select(rank.left, rank.right)

    # calculate kappa
    value <- kappa2(df.input)$value

  }

  else {
    value <- NULL
  }
  
  return(value)

}

# function for creating dataframe of average overlaps
overlap.table <- function(tables, name = "s", am = "log_likelihood", cut_off = 100, p = .95){
  
  values <- c()
  for (i in 2:length(tables)){
    value <- pairwise.overlap(tables,
                              names(tables)[i-1], 
                              names(tables)[i],
                              am = am,
                              cut_off = cut_off,
                              p = p)
    values <- append(values, value)
  }
  g <- data.frame(names(tables)[2:length(tables)], values)
  names(g) <- c(name, "overlap")
  
  return(g)
}
