[pypi-image]: https://badge.fury.io/py/torcheeg.svg
[pypi-url]: https://pypi.python.org/pypi/torcheeg
[docs-image]: https://readthedocs.org/projects/torcheeg/badge/?version=latest
[docs-url]: https://torcheeg.readthedocs.io/en/latest/?badge=latest

![TorchEEG Logo](https://github.com/tczhangzhi/torcheeg/blob/main/docs/source/_static/torcheeg_logo_dark.png)

--------------------------------------------------------------------------------

[![PyPI Version][pypi-image]][pypi-url]
[![Docs Status][docs-image]][docs-url]

**[Documentation](https://torcheeg.readthedocs.io/)** | **[TorchEEG Examples](https://github.com/tczhangzhi/torcheeg/tree/main/examples)**

TorchEEG is a library built on PyTorch for EEG signal analysis. TorchEEG aims to provide a plug-and-play EEG analysis tool, so that researchers can quickly reproduce EEG analysis work and start new EEG analysis research without paying attention to technical details unrelated to the research focus.

TorchEEG specifies a unified data input-output format (IO) and implement commonly used EEG databases, allowing users to quickly access benchmark datasets and define new custom datasets. The datasets that have been defined so far include emotion recognition and so on. According to papers published in the field of EEG analysis, TorchEEG provides data preprocessing methods commonly used for EEG signals, and provides plug-and-play API for both offline and online pre-proocessing. Offline processing allow users to process once and use any times, speeding up the training process. Online processing allows users to save time when creating new data processing methods. TorchEEG also provides deep learning models following published papers for EEG analysis, including convolutional neural networks, graph convolutional neural networks, and Transformers.

## Installation

### Pip

TorchEEG also allows pip-based installation, please use the following command:

```shell
pip install torcheeg
```

### Nightly

In case you want to experiment with the latest TorchEEG features which are not fully released yet, please run the following command to install from the main branch on github:

```shell
pip install git+https://github.com/tczhangzhi/torcheeg.git
```

## More About TorchEEG

At a granular level, PyTorch is a library that consists of the following components:

| Component | Description |
| ---- | --- |
| torcheeg.io | A set of unified input and output API is used to store the processing results of various EEG databases for more efficient and convenient use. |
| torcheeg.datasets | The packaged benchmark dataset implementation provides a multi-process preprocessing interface. |
| torcheeg.transforms | Rich EEG preprocessing methods help users extract features, construct EEG signal representations, and connect to commonly used deep learning libraries. |
| torcheeg.model_selection | Rich dataset partitioning methods for users to experiment with different settings. |
| torcheeg.models | Rich baseline method reproduction. |
| torcheeg.utils | Other helper functions. |

## Quickstart

In this quick tour, we highlight the ease of starting an EEG analysis research with only modifying a few lines of [PyTorch tutorial](https://pytorch.org/tutorials/beginner/basics/quickstart_tutorial.html). 

The `torcheeg.datasets` module contains dataset objects for many real-world EEG data, such as DEAP, DREAMER, and SEED. In this tutorial, we use the `DEAP` dataset. Each `Dataset` contains three parameters: `online_transform`, `offline_transform`, and `target_transform`, which are used to modify samples and labels, respectively.

```python
from torcheeg.datasets import DEAPDataset
from torcheeg.datasets.constants.emotion_recognition.deap import DEAP_CHANNEL_LOCATION_DICT

dataset = DEAPDataset(io_path=f'./deap',
                      root_path='./data_preprocessed_python',
                      offline_transform=transforms.Compose([
                          transforms.BandDifferentialEntropy(),
                          transforms.ToGrid(DEAP_CHANNEL_LOCATION_DICT)
                      ]),
                      online_transform=transforms.ToTensor(),
                      label_transform=transforms.Compose([
                          transforms.Select('valence'),
                          transforms.Binary(5.0),
                      ]))
```

Here, `offline_transform` is used to modify samples when generating and processing intermediate results, `online_transform` is used to modify samples during operation, and`target_transform` is used to modify labels. We strongly recommend placing time-consuming numpy transforms in `offline_transform`, and pytorch and data augmentation related transforms in `online_transform`.

Next, we need to divide the dataset into a training set and a test set. In the field of EEG analysis, commonly used data partitioning methods include k-fold cross-validation and leave-one-out cross-validation. In this tutorial, we use k-fold cross-validation on the entire dataset (`KFoldDataset`) as an example for dataset partitioning.

```python
from torcheeg.model_selection import KFoldDataset

k_fold = KFoldDataset(n_splits=5, split_path='./split', shuffle=True)
```

Let's define a simple but effective CNN model:

```python
class CNN(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Sequential(
            nn.ZeroPad2d((1, 2, 1, 2)),
            nn.Conv2d(4, 64, kernel_size=4, stride=1),
            nn.ReLU()
        )
        self.conv2 = nn.Sequential(
            nn.ZeroPad2d((1, 2, 1, 2)),
            nn.Conv2d(64, 128, kernel_size=4, stride=1),
            nn.ReLU()
        )
        self.conv3 = nn.Sequential(
            nn.ZeroPad2d((1, 2, 1, 2)),
            nn.Conv2d(128, 256, kernel_size=4, stride=1),
            nn.ReLU()
        )
        self.conv4 = nn.Sequential(
            nn.ZeroPad2d((1, 2, 1, 2)),
            nn.Conv2d(256, 64, kernel_size=4, stride=1),
            nn.ReLU()
        )

        self.lin1 = nn.Linear(9 * 9 * 64, 1024)
        self.lin2 = nn.Linear(1024, 2)

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)

        x = x.flatten(start_dim=1)
        x = self.lin1(x)
        x = self.lin2(x)
        return x
```

During the research, we may also use other GNN or Transformer-based models and build more complex projects. Please refer to the examples in the `exmaples/` folder.

The training and validation scripts for the model are taken from the PyTorch tutorial without much modification. The only thing worth noting is that the `Dataset` provides three values when it is traversed, namely the EEG signal (denoted by `X` in the code), the baseline signal (denoted by `b` in the code), and the sample label (denoted by `y` in the code). In particular, to achieve baseline removal, we subtract the baseline signal from the original signal as input to the model (see `pred = model(X - b)`).

```python
device = "cuda" if torch.cuda.is_available() else "cpu"
model = CNN().to(device)

loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)

batch_size = 64

def train(dataloader, model, loss_fn, optimizer):
    size = len(dataloader.dataset)
    model.train()
    for batch_idx, batch in enumerate(dataloader):
        X = batch[0].to(device)
        b = batch[1].to(device)
        y = batch[2].to(device)

        # Compute prediction error
        pred = model(X - b)
        loss = loss_fn(pred, y)

        # Backpropagation
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if batch_idx % 100 == 0:
            loss, current = loss.item(), batch_idx * len(X)
            print(f"loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")


def valid(dataloader, model, loss_fn):
    size = len(dataloader.dataset)
    num_batches = len(dataloader)
    model.eval()
    val_loss, correct = 0, 0
    with torch.no_grad():
        for batch in dataloader:
            X = batch[0].to(device)
            b = batch[1].to(device)
            y = batch[2].to(device)

            pred = model(X - b)
            val_loss += loss_fn(pred, y).item()
            correct += (pred.argmax(1) == y).type(torch.float).sum().item()
    val_loss /= num_batches
    correct /= size
    print(
        f"Test Error: \n Accuracy: {(100*correct):>0.1f}%, Avg loss: {val_loss:>8f} \n"
    )


for i, (train_dataset, val_dataset) in enumerate(k_fold.split(dataset)):
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    epochs = 5
    for t in range(epochs):
        print(f"Epoch {t+1}\n-------------------------------")
        train(train_loader, model, loss_fn, optimizer)
        valid(val_loader, model, loss_fn)
    print("Done!")
```

For more specific usage of each module, please refer to [the documentation]((https://torcheeg.readthedocs.io/)).

## Releases and Contributing

TorchEEG is currently in beta; Please let us know if you encounter a bug by filing an issue. We also appreciate all contributions.

If you would like to contribute new datasets, deep learning methods, and extensions to the core, please first open an issue and then send a PR. If you are planning to contribute back bug fixes, please do so without any further discussion.

## License

TorchEEG has a MIT license, as found in the [LICENSE](https://github.com/tczhangzhi/torcheeg/blob/main/LICENSE) file.