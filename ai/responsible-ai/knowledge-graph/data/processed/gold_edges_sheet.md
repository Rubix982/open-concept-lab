# Gold edge labeling sheet

For each pair, write ONE label after `RELATION:` from this set (A→B direction):

- SUPPORTS                — A's result/evidence backs B's claim
- CONTRADICTS             — A's finding is logically incompatible with B's
- REFINES                 — A improves / generalizes / extends B's method or result
- ADDRESSES_SAME_PROBLEM  — A and B tackle the same problem, different approaches (symmetric)
- USES                    — A uses a method/dataset/result introduced by B
- RELATED                 — same topic, no stronger typed relation (symmetric)
- NONE                    — not meaningfully related (should be pruned)

Just fill the RELATION line. Direction is secondary — assume A→B; for a clearly
backwards directional case you may write e.g. `REFINES (B→A)`.

_37 pairs to label (deduped from 50)._

## [0]  (cosine similarity 0.753)
**A** — _The Graph Neural Network Model_
> In this paper, we propose a new neural network model, called graph neural network (GNN) model, that extends existing neural network methods for processing the data represented in graph domains.

**B** — _A Comprehensive Survey on Graph Neural Networks_
> In this article, we provide a comprehensive overview of graph neural networks (GNNs) in data mining and machine learning fields.

RELATION: SUPPORTS

## [1]  (cosine similarity 0.711)
**A** — _The Graph Neural Network Model_
> In this paper, we propose a new neural network model, called graph neural network (GNN) model, that extends existing neural network methods for processing the data represented in graph domains.

**B** — _Heterogeneous Graph Neural Network_
> In this paper, we propose HetGNN, a heterogeneous graph neural network model, to resolve this issue.

RELATION: ADDRESSES_SAME_PROBLEM

## [2]  (cosine similarity 0.675)
**A** — _The Graph Neural Network Model_
> In this paper, we propose a new neural network model, called graph neural network (GNN) model, that extends existing neural network methods for processing the data represented in graph domains.

**B** — _Graph Structure Learning for Robust Graph Neural Networks_
> In particular, we propose a general framework Pro-GNN, which can jointly learn a structural graph and a robust graph neural network model from the perturbed graph guided by these properties.

RELATION: REFINES

## [3]  (cosine similarity 0.669)
**A** — _The Graph Neural Network Model_
> In this paper, we propose a new neural network model, called graph neural network (GNN) model, that extends existing neural network methods for processing the data represented in graph domains.

**B** — _Measuring and Relieving the Over-Smoothing Problem for Graph Neural Networks from the Topological View_
> Extensive experiments on 7 widely-used graph datasets with 10 typical GNN models show that the two proposed methods are effective for relieving the over-smoothing issue, thus improving the performance of various GNN models.

RELATION: REFINES

## [4]  (cosine similarity 0.664)
**A** — _A Comprehensive Survey on Graph Neural Networks_
> In this article, we provide a comprehensive overview of graph neural networks (GNNs) in data mining and machine learning fields.

**B** — _How Powerful are Graph Neural Networks?_
> Our results characterize the discriminative power of popular GNN variants, such as Graph Convolutional Networks and GraphSAGE, and show that they cannot learn to distinguish certain simple graph structures.

RELATION: USES

## [5]  (cosine similarity 0.659)
**A** — _A Comprehensive Survey on Graph Neural Networks_
> In this article, we provide a comprehensive overview of graph neural networks (GNNs) in data mining and machine learning fields.

**B** — _Towards Deeper Graph Neural Networks_
> In this work, we study this observation systematically and develop new insights towards deeper graph neural networks.

RELATION: REFINES

## [6]  (cosine similarity 0.638)
**A** — _A Comprehensive Survey on Graph Neural Networks_
> In this article, we provide a comprehensive overview of graph neural networks (GNNs) in data mining and machine learning fields.

**B** — _Heterogeneous Graph Neural Network_
> In this paper, we propose HetGNN, a heterogeneous graph neural network model, to resolve this issue.

RELATION: ADDRESSES_SAME_PROBLEM

## [7]  (cosine similarity 0.636)
**A** — _A Comprehensive Survey on Graph Neural Networks_
> In this article, we provide a comprehensive overview of graph neural networks (GNNs) in data mining and machine learning fields.

**B** — _MAGNN: Metapath Aggregated Graph Neural Network for Heterogeneous Graph Embedding_
> Extensive experiments on three real-world heterogeneous graph datasets for node classification, node clustering, and link prediction show that MAGNN achieves more accurate prediction results than state-of-the-art baselines.

RELATION: REFINES

## [8]  (cosine similarity 0.671)
**A** — _A Comprehensive Survey on Graph Neural Networks_
> We propose a new taxonomy to divide the state-of-the-art GNNs into four categories, namely, recurrent GNNs, convolutional GNNs, graph autoencoders, and spatial-temporal GNNs.

**B** — _Graph Neural Networks in Recommender Systems: A Survey_
> Moreover, we systematically analyze the challenges of applying GNN on different types of data and discuss how existing works in this field address these challenges.

RELATION: REFINES

## [9]  (cosine similarity 0.649)
**A** — _A Comprehensive Survey on Graph Neural Networks_
> We propose a new taxonomy to divide the state-of-the-art GNNs into four categories, namely, recurrent GNNs, convolutional GNNs, graph autoencoders, and spatial-temporal GNNs.

**B** — _Graph neural networks: A review of methods and applications_
> In this survey, we propose a general design pipeline for GNN models and discuss the variants of each component, systematically categorize the applications, and propose four open problems for future research.

RELATION: REFINES

## [10]  (cosine similarity 0.631)
**A** — _A Comprehensive Survey on Graph Neural Networks_
> We propose a new taxonomy to divide the state-of-the-art GNNs into four categories, namely, recurrent GNNs, convolutional GNNs, graph autoencoders, and spatial-temporal GNNs.

**B** — _How Powerful are Graph Neural Networks?_
> Our results characterize the discriminative power of popular GNN variants, such as Graph Convolutional Networks and GraphSAGE, and show that they cannot learn to distinguish certain simple graph structures.

RELATION: REFINES

## [11]  (cosine similarity 0.612)
**A** — _A Comprehensive Survey on Graph Neural Networks_
> We propose a new taxonomy to divide the state-of-the-art GNNs into four categories, namely, recurrent GNNs, convolutional GNNs, graph autoencoders, and spatial-temporal GNNs.

**B** — _How Powerful are Graph Neural Networks?_
> Here, we present a theoretical framework for analyzing the expressive power of GNNs to capture different graph structures.

RELATION: REFINES

## [12]  (cosine similarity 0.636)
**A** — _A Comprehensive Survey on Graph Neural Networks_
> Finally, we propose potential research directions in this rapidly growing field.

**B** — _Graph Neural Networks in Recommender Systems: A Survey_
> Furthermore, we state new perspectives pertaining to the development of this field.

RELATION: USES

## [13]  (cosine similarity 0.816)
**A** — _Graph neural networks: A review of methods and applications_
> In this survey, we propose a general design pipeline for GNN models and discuss the variants of each component, systematically categorize the applications, and propose four open problems for future research.

**B** — _Pitfalls of Graph Neural Network Evaluation_
> In this paper we show that existing evaluation strategies for GNN models have serious shortcomings.

RELATION: CONTRADICTS

## [14]  (cosine similarity 0.745)
**A** — _Graph neural networks: A review of methods and applications_
> In this survey, we propose a general design pipeline for GNN models and discuss the variants of each component, systematically categorize the applications, and propose four open problems for future research.

**B** — _Graph Neural Networks in Recommender Systems: A Survey_
> Moreover, we systematically analyze the challenges of applying GNN on different types of data and discuss how existing works in this field address these challenges.

RELATION: REFINES

## [15]  (cosine similarity 0.721)
**A** — _Graph neural networks: A review of methods and applications_
> In this survey, we propose a general design pipeline for GNN models and discuss the variants of each component, systematically categorize the applications, and propose four open problems for future research.

**B** — _Pitfalls of Graph Neural Network Evaluation_
> We perform a thorough empirical evaluation of four prominent GNN models and show that considering different splits of the data leads to dramatically different rankings of models.

RELATION: USES

## [16]  (cosine similarity 0.667)
**A** — _Graph neural networks: A review of methods and applications_
> In this survey, we propose a general design pipeline for GNN models and discuss the variants of each component, systematically categorize the applications, and propose four open problems for future research.

**B** — _Pitfalls of Graph Neural Network Evaluation_
> Even more importantly, our findings suggest that simpler GNN architectures are able to outperform the more sophisticated ones if the hyperparameters and the training procedure are tuned fairly for all models.

RELATION: REFINES

## [17]  (cosine similarity 0.656)
**A** — _Graph neural networks: A review of methods and applications_
> In this survey, we propose a general design pipeline for GNN models and discuss the variants of each component, systematically categorize the applications, and propose four open problems for future research.

**B** — _Measuring and Relieving the Over-Smoothing Problem for Graph Neural Networks from the Topological View_
> In this work, we present a systematic and quantitative study on the over-smoothing issue of GNNs.

RELATION: RELATED

## [18]  (cosine similarity 0.577)
**A** — _The Graph Neural Network Model_
> In this paper, we propose a new neural network model, called graph neural network (GNN) model, that extends existing neural network methods for processing the data represented in graph domains.

**B** — _Targeted Branching for the Maximum Independent Set Problem Using Graph Neural Networks_
> In this work, we present a graph neural network approach for selecting the next branching vertex.

RELATION: RELATED

## [19]  (cosine similarity 0.724)
**A** — _Graph Neural Networks for Social Recommendation_
> To address the three aforementioned challenges simultaneously, in this paper, we present a novel graph neural network framework (GraphRec) for social recommendations.

**B** — _Sequential Recommendation with Graph Neural Networks_
> In this work, we propose a graph neural network model called SURGE (short forSeqUential Recommendation with Graph neural nEtworks) to address these two issues.

RELATION: ADDRESSES_SAME_PROBLEM

## [20]  (cosine similarity 0.715)
**A** — _Graph Neural Networks for Social Recommendation_
> To address the three aforementioned challenges simultaneously, in this paper, we present a novel graph neural network framework (GraphRec) for social recommendations.

**B** — _Knowledge-aware Graph Neural Networks with Label Smoothness Regularization for Recommender Systems_
> Here we propose Knowledge-aware Graph Neural Networks with Label Smoothness regularization (KGNN-LS) to provide better recommendations.

RELATION: ADDRESSES_SAME_PROBLEM

## [21]  (cosine similarity 0.675)
**A** — _Graph Neural Networks for Social Recommendation_
> To address the three aforementioned challenges simultaneously, in this paper, we present a novel graph neural network framework (GraphRec) for social recommendations.

**B** — _Graph Convolutional Neural Networks for Web-Scale Recommender Systems_
> To our knowledge, this is by far the largest application of deep graph embeddings to date and paves the way for a new generation of web-scale recommender systems based on graph convolutional architectures.

RELATION: REFINES

## [22]  (cosine similarity 0.64)
**A** — _Graph Neural Networks for Social Recommendation_
> To address the three aforementioned challenges simultaneously, in this paper, we present a novel graph neural network framework (GraphRec) for social recommendations.

**B** — _Session-Based Recommendation with Graph Neural Networks_
> To obtain accurate item embedding and take complex transitions of items into account, we propose a novel method, i.e. Session-based Recommendation with Graph Neural Networks, SR-GNN for brevity.

RELATION: ADDRESSES_SAME_PROBLEM

## [23]  (cosine similarity 0.614)
**A** — _Graph Neural Networks for Social Recommendation_
> To address the three aforementioned challenges simultaneously, in this paper, we present a novel graph neural network framework (GraphRec) for social recommendations.

**B** — _Graph Convolutional Neural Networks for Web-Scale Recommender Systems_
> We show how GCN embeddings can be used to make high-quality recommendations in various settings at Pinterest, which has a massive underlying graph with 3 billion nodes representing pins and boards, and 17 billion edges.

RELATION: RELATED

## [24]  (cosine similarity 0.613)
**A** — _Graph Neural Networks for Social Recommendation_
> To address the three aforementioned challenges simultaneously, in this paper, we present a novel graph neural network framework (GraphRec) for social recommendations.

**B** — _Graph Neural Networks for Social Recommendation_
> In particular, we provide a principled approach to jointly capture interactions and opinions in the user-item graph and propose the framework GraphRec, which coherently models two graphs and heterogeneous strengths.

RELATION: REFINES

## [25]  (cosine similarity 0.669)
**A** — _Graph Neural Networks for Social Recommendation_
> Extensive experiments on two real-world datasets demonstrate the effectiveness of the proposed framework GraphRec.

**B** — _GNNExplainer: Generating Explanations for Graph Neural Networks_
> Experiments on synthetic and real-world graphs show that our approach can identify important graph structures as well as node features, and outperforms baselines by 17.1% on average.

RELATION: REFINES

## [26]  (cosine similarity 0.634)
**A** — _Graph Neural Networks for Social Recommendation_
> Extensive experiments on two real-world datasets demonstrate the effectiveness of the proposed framework GraphRec.

**B** — _How Powerful are Graph Neural Networks?_
> We empirically validate our theoretical findings on a number of graph classification benchmarks, and demonstrate that our model achieves state-of-the-art performance.

RELATION: USES

## [27]  (cosine similarity 0.621)
**A** — _Graph Neural Networks for Social Recommendation_
> Extensive experiments on two real-world datasets demonstrate the effectiveness of the proposed framework GraphRec.

**B** — _GNNExplainer: Generating Explanations for Graph Neural Networks._
> Experiments on synthetic and real-world graphs show that our approach can identify important graph structures as well as node features, and outperforms alternative baseline approaches by up to 43.0% in explanation accuracy.

RELATION: REFINES

## [28]  (cosine similarity 0.607)
**A** — _Graph Neural Networks for Social Recommendation_
> Extensive experiments on two real-world datasets demonstrate the effectiveness of the proposed framework GraphRec.

**B** — _MAGNN: Metapath Aggregated Graph Neural Network for Heterogeneous Graph Embedding_
> Extensive experiments on three real-world heterogeneous graph datasets for node classification, node clustering, and link prediction show that MAGNN achieves more accurate prediction results than state-of-the-art baselines.

RELATION: ADDRESSES_SAME_PROBLEM

## [29]  (cosine similarity 0.598)
**A** — _Graph Neural Networks for Social Recommendation_
> Extensive experiments on two real-world datasets demonstrate the effectiveness of the proposed framework GraphRec.

**B** — _Measuring and Relieving the Over-Smoothing Problem for Graph Neural Networks from the Topological View_
> Extensive experiments on 7 widely-used graph datasets with 10 typical GNN models show that the two proposed methods are effective for relieving the over-smoothing issue, thus improving the performance of various GNN models.

RELATION: REFINES

## [30]  (cosine similarity 0.62)
**A** — _Heterogeneous Graph Neural Network_
> In this paper, we propose HetGNN, a heterogeneous graph neural network model, to resolve this issue.

**B** — _Heterogeneous Graph Neural Network_
> Extensive experiments on several datasets demonstrate that HetGNN can outperform state-of-the-art baselines in various graph mining tasks, i.e., link prediction, recommendation, node classification & clustering and inductive node classification & clustering.

RELATION: USES

## [31]  (cosine similarity 0.618)
**A** — _Heterogeneous Graph Neural Network_
> In this paper, we propose HetGNN, a heterogeneous graph neural network model, to resolve this issue.

**B** — _Connecting the Dots: Multivariate Time Series Forecasting with Graph Neural Networks_
> In this paper, we propose a general graph neural network framework designed specifically for multivariate time series data.

RELATION: RELATED

## [32]  (cosine similarity 0.705)
**A** — _Heterogeneous Graph Neural Network_
> Extensive experiments on several datasets demonstrate that HetGNN can outperform state-of-the-art baselines in various graph mining tasks, i.e., link prediction, recommendation, node classification & clustering and inductive node classification & clustering.

**B** — _MAGNN: Metapath Aggregated Graph Neural Network for Heterogeneous Graph Embedding_
> Extensive experiments on three real-world heterogeneous graph datasets for node classification, node clustering, and link prediction show that MAGNN achieves more accurate prediction results than state-of-the-art baselines.

RELATION: REFINES

## [33]  (cosine similarity 0.653)
**A** — _Heterogeneous Graph Neural Network_
> Extensive experiments on several datasets demonstrate that HetGNN can outperform state-of-the-art baselines in various graph mining tasks, i.e., link prediction, recommendation, node classification & clustering and inductive node classification & clustering.

**B** — _How Powerful are Graph Neural Networks?_
> We empirically validate our theoretical findings on a number of graph classification benchmarks, and demonstrate that our model achieves state-of-the-art performance.

RELATION: USES

## [34]  (cosine similarity 0.629)
**A** — _A Comprehensive Survey on Graph Neural Networks_
> In this article, we provide a comprehensive overview of graph neural networks (GNNs) in data mining and machine learning fields.

**B** — _Heterogeneous Graph Neural Network_
> Extensive experiments on several datasets demonstrate that HetGNN can outperform state-of-the-art baselines in various graph mining tasks, i.e., link prediction, recommendation, node classification & clustering and inductive node classification & clustering.

RELATION: USES

## [35]  (cosine similarity 0.693)
**A** — _Session-Based Recommendation with Graph Neural Networks_
> To obtain accurate item embedding and take complex transitions of items into account, we propose a novel method, i.e. Session-based Recommendation with Graph Neural Networks, SR-GNN for brevity.

**B** — _Session-Based Recommendation with Graph Neural Networks_
> Extensive experiments conducted on two real datasets show that SR-GNN evidently outperforms the state-of-the-art session-based recommendation methods consistently.

RELATION: USES

## [36]  (cosine similarity 0.636)
**A** — _Session-Based Recommendation with Graph Neural Networks_
> To obtain accurate item embedding and take complex transitions of items into account, we propose a novel method, i.e. Session-based Recommendation with Graph Neural Networks, SR-GNN for brevity.

**B** — _Graph Convolutional Neural Networks for Web-Scale Recommender Systems_
> To our knowledge, this is by far the largest application of deep graph embeddings to date and paves the way for a new generation of web-scale recommender systems based on graph convolutional architectures.

RELATION: NONE
